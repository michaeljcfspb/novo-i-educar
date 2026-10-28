from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from apps.schools.models import Serie, Turma
from .models import Matricula, MatriculaTurma, SituacaoMatricula


class MatriculaTurmaSerializer(serializers.ModelSerializer):
    turma_nome = serializers.CharField(source="turma.nome", read_only=True)

    class Meta:
        model = MatriculaTurma
        fields = ("id", "turma", "turma_nome", "data_enturmacao", "ativo", "sequencial")
        read_only_fields = ("id",)


class MatriculaSerializer(serializers.ModelSerializer):
    aluno_nome = serializers.CharField(source="aluno.pessoa.nome", read_only=True)
    escola_nome = serializers.CharField(source="escola.nome", read_only=True)
    serie_nome = serializers.CharField(source="serie.nome", read_only=True)
    situacao_display = serializers.CharField(source="get_situacao_display", read_only=True)
    enturmacoes = MatriculaTurmaSerializer(many=True, read_only=True)

    class Meta:
        model = Matricula
        fields = (
            "id", "aluno", "aluno_nome", "escola", "escola_nome", "serie", "serie_nome", "curso",
            "ano", "data_matricula", "situacao", "situacao_display", "ativo", "observacao",
            "enturmacoes", "criado_em", "atualizado_em",
        )
        read_only_fields = ("id", "criado_em", "atualizado_em")

    def validate(self, attrs):
        serie = attrs.get("serie", getattr(self.instance, "serie", None))
        curso = attrs.get("curso", getattr(self.instance, "curso", None))
        if serie and curso and serie.curso_id != curso.id:
            raise serializers.ValidationError({"curso": "O curso deve ser o mesmo da série."})
        return attrs

    def create(self, validated_data):
        if not validated_data.get("data_matricula"):
            validated_data["data_matricula"] = timezone.localdate()
        return super().create(validated_data)


class EnturmarSerializer(serializers.Serializer):
    turma = serializers.PrimaryKeyRelatedField(queryset=Turma.objects.all())
    data_enturmacao = serializers.DateField(required=False)

    def validate_turma(self, turma):
        matricula = self.context["matricula"]
        if turma.escola_id != matricula.escola_id:
            raise serializers.ValidationError("A turma pertence a outra escola.")
        if turma.ano != matricula.ano:
            raise serializers.ValidationError("O ano da turma difere do ano da matrícula.")
        if turma.serie_id != matricula.serie_id:
            raise serializers.ValidationError("A turma pertence a outra série.")
        if turma.vagas_disponiveis <= 0:
            raise serializers.ValidationError("A turma não possui vagas disponíveis.")
        return turma

    @transaction.atomic
    def create(self, validated_data):
        matricula = self.context["matricula"]
        enturmacao = MatriculaTurma.objects.create(
            matricula=matricula,
            turma=validated_data["turma"],
            data_enturmacao=validated_data.get("data_enturmacao") or timezone.localdate(),
        )
        return enturmacao


class AlterarSituacaoSerializer(serializers.Serializer):
    situacao = serializers.ChoiceField(choices=SituacaoMatricula.choices)

    def validate_situacao(self, situacao):
        matricula = self.context["matricula"]
        if matricula.situacao == SituacaoMatricula.CANCELADA and situacao != SituacaoMatricula.CANCELADA:
            raise serializers.ValidationError("Matrícula cancelada não pode ser reaberta.")
        return situacao


class RemanejarSerializer(serializers.Serializer):
    turma = serializers.PrimaryKeyRelatedField(queryset=Turma.objects.all())
    data = serializers.DateField(required=False)

    def validate_turma(self, turma):
        matricula = self.context["matricula"]
        if turma.escola_id != matricula.escola_id:
            raise serializers.ValidationError("A turma pertence a outra escola.")
        if turma.ano != matricula.ano:
            raise serializers.ValidationError("O ano da turma difere do ano da matrícula.")
        if turma.serie_id != matricula.serie_id:
            raise serializers.ValidationError("A turma pertence a outra série.")
        if turma.vagas_disponiveis <= 0:
            raise serializers.ValidationError("A turma não possui vagas disponíveis.")
        return turma

    @transaction.atomic
    def create(self, validated_data):
        from django.utils import timezone

        matricula = self.context["matricula"]
        atuais = matricula.enturmacoes.filter(ativo=True)
        sequencial = (atuais.order_by("-sequencial").first().sequencial if atuais.exists() else 0) + 1
        atuais.update(ativo=False)
        return MatriculaTurma.objects.create(
            matricula=matricula,
            turma=validated_data["turma"],
            data_enturmacao=validated_data.get("data") or timezone.localdate(),
            sequencial=sequencial,
        )


class ReclassificarSerializer(serializers.Serializer):
    serie = serializers.PrimaryKeyRelatedField(queryset=Serie.objects.all())
    observacao = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_serie(self, serie):
        matricula = self.context["matricula"]
        if serie.curso.instituicao_id != matricula.escola.instituicao_id:
            raise serializers.ValidationError("A série pertence a outra instituição.")
        return serie

    @transaction.atomic
    def create(self, validated_data):
        matricula = self.context["matricula"]
        matricula.serie = validated_data["serie"]
        matricula.curso = validated_data["serie"].curso
        matricula.observacao = (
            f"{matricula.observacao}\nReclassificado para {matricula.serie}".strip()
        )
        matricula.save(update_fields=["serie", "curso", "observacao", "atualizado_em"])
        matricula.enturmacoes.filter(ativo=True).update(ativo=False)
        return matricula
