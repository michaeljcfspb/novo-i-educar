from django.contrib import admin

from .models import EntregaWebhook, Importacao, Webhook


@admin.register(Importacao)
class ImportacaoAdmin(admin.ModelAdmin):
    list_display = ("arquivo_nome", "tipo", "status", "total_sucessos", "total_erros", "criado_em")
    list_filter = ("status", "tipo")


@admin.register(Webhook)
class WebhookAdmin(admin.ModelAdmin):
    list_display = ("nome", "url", "ativo")


@admin.register(EntregaWebhook)
class EntregaWebhookAdmin(admin.ModelAdmin):
    list_display = ("webhook", "evento", "sucesso", "status_code", "criado_em")
    list_filter = ("sucesso", "evento")
