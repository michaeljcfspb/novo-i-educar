from rest_framework import serializers

from .models import ExportacaoCenso


class ExportacaoCensoSerializer(serializers.ModelSerializer):
    escola_nome = serializers.CharField(source="escola.nome", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = ExportacaoCenso
        fields = (
            "id", "escola", "escola_nome", "ano", "versao", "status", "status_display",
            "total_alunos", "total_turmas", "pendencias", "payload", "criado_em",
        )
        read_only_fields = fields


class GerarCensoSerializer(serializers.Serializer):
    escola = serializers.IntegerField()
    ano = serializers.IntegerField(min_value=2000, max_value=2100)
