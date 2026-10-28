from decimal import Decimal

from rest_framework import serializers

from .models import Nota, PeriodoAvaliacao, RegraAvaliacao, TipoNota


class RegraAvaliacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegraAvaliacao
        fields = (
            "id", "nome", "tipo_media", "nota_maxima", "media_aprovacao", "media_recuperacao",
            "percentual_frequencia", "permite_recuperacao", "casas_decimais",
        )
        read_only_fields = ("id",)

    def validate(self, attrs):
        aprovacao = attrs.get("media_aprovacao", getattr(self.instance, "media_aprovacao", None))
        recuperacao = attrs.get(
            "media_recuperacao", getattr(self.instance, "media_recuperacao", None)
        )
        maxima = attrs.get("nota_maxima", getattr(self.instance, "nota_maxima", None))
        if recuperacao is not None and aprovacao is not None and recuperacao > aprovacao:
            raise serializers.ValidationError(
                {"media_recuperacao": "A média de recuperação não pode exceder a de aprovação."}
            )
        if maxima is not None and aprovacao is not None and maxima < aprovacao:
            raise serializers.ValidationError(
                {"nota_maxima": "A nota máxima deve ser maior que a média de aprovação."}
            )
        return attrs


class PeriodoAvaliacaoSerializer(serializers.ModelSerializer):
    ano = serializers.IntegerField(source="ano_letivo.ano", read_only=True)

    class Meta:
        model = PeriodoAvaliacao
        fields = ("id", "ano_letivo", "ano", "nome", "ordem", "data_inicio", "data_fim", "peso")
        read_only_fields = ("id", "ano")

    def validate(self, attrs):
        inicio = attrs.get("data_inicio", getattr(self.instance, "data_inicio", None))
        fim = attrs.get("data_fim", getattr(self.instance, "data_fim", None))
        if inicio and fim and fim < inicio:
            raise serializers.ValidationError({"data_fim": "O término não pode ser anterior ao início."})
        return attrs


class NotaSerializer(serializers.ModelSerializer):
    aluno_nome = serializers.CharField(source="matricula.aluno.pessoa.nome", read_only=True)
    disciplina_nome = serializers.CharField(source="turma_disciplina.disciplina.nome", read_only=True)
    periodo_nome = serializers.CharField(source="periodo.nome", read_only=True)

    class Meta:
        model = Nota
        fields = (
            "id", "matricula", "aluno_nome", "turma_disciplina", "disciplina_nome", "periodo",
            "periodo_nome", "tipo", "valor", "observacao",
        )
        read_only_fields = ("id",)

    def validate(self, attrs):
        matricula = attrs.get("matricula", getattr(self.instance, "matricula", None))
        turma_disciplina = attrs.get(
            "turma_disciplina", getattr(self.instance, "turma_disciplina", None)
        )
        periodo = attrs.get("periodo", getattr(self.instance, "periodo", None))
        valor = attrs.get("valor", getattr(self.instance, "valor", None))

        if matricula and turma_disciplina:
            enturmacao = matricula.enturmacoes.filter(ativo=True).first()
            if enturmacao and enturmacao.turma_id != turma_disciplina.turma_id:
                raise serializers.ValidationError(
                    {"turma_disciplina": "A disciplina não pertence à turma atual do aluno."}
                )
        if matricula and periodo and matricula.ano != periodo.ano_letivo.ano:
            raise serializers.ValidationError(
                {"periodo": "O período pertence a outro ano letivo."}
            )

        regra = getattr(matricula.serie, "regra_avaliacao", None) if matricula else None
        if regra and valor is not None:
            if valor < Decimal("0") or valor > regra.nota_maxima:
                raise serializers.ValidationError(
                    {"valor": f"A nota deve estar entre 0 e {regra.nota_maxima}."}
                )
        request = self.context.get("request")
        if request and matricula:
            from apps.core.permissions import validar_escola_do_usuario

            validar_escola_do_usuario(request.user, matricula.escola_id)
            if request.user.perfil == "professor" and request.user.servidor_id:
                if turma_disciplina and turma_disciplina.professor_id != request.user.servidor_id:
                    raise serializers.ValidationError(
                        {"turma_disciplina": "Você só pode lançar notas das suas turmas."}
                    )
        return attrs


class RegistroNotaSerializer(serializers.Serializer):
    matricula = serializers.IntegerField()
    valor = serializers.DecimalField(max_digits=5, decimal_places=2)
    observacao = serializers.CharField(required=False, allow_blank=True, default="")


class LoteNotasSerializer(serializers.Serializer):
    turma_disciplina = serializers.IntegerField()
    periodo = serializers.IntegerField()
    tipo = serializers.ChoiceField(choices=TipoNota.choices, default=TipoNota.NORMAL)
    registros = RegistroNotaSerializer(many=True)
