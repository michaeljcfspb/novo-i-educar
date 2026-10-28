from rest_framework import serializers

from apps.core.permissions import validar_escola_do_usuario
from .models import Documento, HistoricoDisciplina, HistoricoEscolar, Transferencia


class HistoricoDisciplinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoricoDisciplina
        fields = ("id", "nome_disciplina", "carga_horaria", "media", "frequencia", "situacao")


class HistoricoEscolarSerializer(serializers.ModelSerializer):
    aluno_nome = serializers.CharField(source="aluno.pessoa.nome", read_only=True)
    escola_nome = serializers.CharField(source="escola.nome", read_only=True)
    serie_nome = serializers.CharField(source="serie.nome", read_only=True)
    disciplinas = HistoricoDisciplinaSerializer(many=True, read_only=True)
    situacao_display = serializers.CharField(source="get_situacao_display", read_only=True)

    class Meta:
        model = HistoricoEscolar
        fields = (
            "id", "aluno", "aluno_nome", "matricula", "escola", "escola_nome", "serie",
            "serie_nome", "ano", "carga_horaria_total", "dias_letivos", "frequencia_percentual",
            "media_geral", "situacao", "situacao_display", "observacoes", "disciplinas",
            "criado_em",
        )
        read_only_fields = (
            "id", "carga_horaria_total", "dias_letivos", "frequencia_percentual", "media_geral",
            "situacao", "criado_em",
        )


class TransferenciaSerializer(serializers.ModelSerializer):
    aluno_nome = serializers.CharField(source="matricula.aluno.pessoa.nome", read_only=True)
    escola_origem_nome = serializers.CharField(source="escola_origem.nome", read_only=True, default=None)
    escola_destino_nome = serializers.CharField(source="escola_destino.nome", read_only=True, default=None)
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)

    class Meta:
        model = Transferencia
        fields = (
            "id", "matricula", "aluno_nome", "tipo", "tipo_display", "data", "escola_origem",
            "escola_origem_nome", "escola_destino", "escola_destino_nome", "motivo",
            "observacao", "criado_em",
        )
        read_only_fields = ("id", "escola_origem", "criado_em")

    def validate(self, attrs):
        matricula = attrs.get("matricula", getattr(self.instance, "matricula", None))
        tipo = attrs.get("tipo", getattr(self.instance, "tipo", None))
        destino = attrs.get("escola_destino", getattr(self.instance, "escola_destino", None))
        if tipo in {"saida", "interna"} and not destino:
            raise serializers.ValidationError(
                {"escola_destino": "Informe a escola de destino."}
            )
        request = self.context.get("request")
        if request and matricula:
            validar_escola_do_usuario(request.user, matricula.escola_id)
        return attrs


class DocumentoSerializer(serializers.ModelSerializer):
    aluno_nome = serializers.CharField(source="aluno.pessoa.nome", read_only=True)
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)

    class Meta:
        model = Documento
        fields = (
            "id", "aluno", "aluno_nome", "matricula", "tipo", "tipo_display", "numero",
            "titulo", "corpo", "emitido_em",
        )
        read_only_fields = ("id", "numero", "titulo", "corpo", "emitido_em")


class EmitirDocumentoSerializer(serializers.Serializer):
    aluno = serializers.IntegerField()
    tipo = serializers.ChoiceField(choices=Documento._meta.get_field("tipo").choices)
    matricula = serializers.IntegerField(required=False, allow_null=True)
