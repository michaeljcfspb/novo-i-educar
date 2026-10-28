"""Importações de planilhas e integrações externas."""
from __future__ import annotations

from django.db import models

from apps.core.models import RegistroAuditavel


class StatusImportacao(models.TextChoices):
    PROCESSANDO = "processando", "Processando"
    CONCLUIDA = "concluida", "Concluída"
    COM_ERROS = "com_erros", "Concluída com erros"
    FALHOU = "falhou", "Falhou"


class Importacao(RegistroAuditavel):
    tipo = models.CharField("tipo", max_length=30, default="alunos")
    arquivo_nome = models.CharField("arquivo", max_length=200)
    status = models.CharField(
        "status", max_length=15, choices=StatusImportacao.choices, default=StatusImportacao.PROCESSANDO
    )
    total_linhas = models.PositiveIntegerField("linhas", default=0)
    total_sucessos = models.PositiveIntegerField("sucessos", default=0)
    total_erros = models.PositiveIntegerField("erros", default=0)
    relatorio = models.JSONField("relatório", default=list, blank=True)

    class Meta:
        verbose_name = "importação"
        verbose_name_plural = "importações"
        ordering = ["-criado_em"]

    def __str__(self) -> str:
        return f"{self.arquivo_nome} · {self.get_status_display()}"


class Webhook(RegistroAuditavel):
    nome = models.CharField("nome", max_length=100)
    url = models.URLField("URL")
    eventos = models.JSONField(
        "eventos", default=list, blank=True,
        help_text="Lista de eventos assinados, ex.: ['matricula.criada', 'transferencia.registrada'].",
    )
    ativo = models.BooleanField("ativo", default=True)

    class Meta:
        verbose_name = "webhook"
        verbose_name_plural = "webhooks"
        ordering = ["nome"]

    def __str__(self) -> str:
        return f"{self.nome} → {self.url}"


class EntregaWebhook(RegistroAuditavel):
    webhook = models.ForeignKey(
        Webhook, verbose_name="webhook", on_delete=models.CASCADE, related_name="entregas"
    )
    evento = models.CharField("evento", max_length=100)
    payload = models.JSONField("payload", default=dict, blank=True)
    status_code = models.PositiveSmallIntegerField("status HTTP", null=True, blank=True)
    sucesso = models.BooleanField("sucesso", default=False)
    erro = models.CharField("erro", max_length=300, blank=True)

    class Meta:
        verbose_name = "entrega de webhook"
        verbose_name_plural = "entregas de webhook"
        ordering = ["-criado_em"]

    def __str__(self) -> str:
        return f"{self.webhook.nome} · {self.evento} · {'ok' if self.sucesso else 'falha'}"
