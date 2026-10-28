from rest_framework import serializers

from .models import EntregaWebhook, Importacao, Webhook


class ImportacaoSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Importacao
        fields = (
            "id", "tipo", "arquivo_nome", "status", "status_display", "total_linhas",
            "total_sucessos", "total_erros", "relatorio", "criado_em",
        )
        read_only_fields = fields


class WebhookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Webhook
        fields = ("id", "nome", "url", "eventos", "ativo", "criado_em")
        read_only_fields = ("id", "criado_em")

    def validate_eventos(self, eventos):
        if not isinstance(eventos, list) or not all(isinstance(item, str) for item in eventos):
            raise serializers.ValidationError("Informe uma lista de eventos (strings).")
        return eventos


class EntregaWebhookSerializer(serializers.ModelSerializer):
    webhook_nome = serializers.CharField(source="webhook.nome", read_only=True)

    class Meta:
        model = EntregaWebhook
        fields = ("id", "webhook", "webhook_nome", "evento", "status_code", "sucesso", "erro", "criado_em")
        read_only_fields = fields
