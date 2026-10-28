"""Exportação do Censo Escolar (INEP)."""
from __future__ import annotations

from django.db import models

from apps.core.models import RegistroAuditavel


class StatusExportacao(models.TextChoices):
    GERADO = "gerado", "Gerado"
    VALIDADO = "validado", "Validado"
    ENVIADO = "enviado", "Enviado"


class ExportacaoCenso(RegistroAuditavel):
    escola = models.ForeignKey(
        "schools.Escola", verbose_name="escola", on_delete=models.CASCADE, related_name="exportacoes_censo"
    )
    ano = models.PositiveSmallIntegerField("ano letivo")
    versao = models.PositiveSmallIntegerField("versão", default=1)
    status = models.CharField(
        "status", max_length=10, choices=StatusExportacao.choices, default=StatusExportacao.GERADO
    )
    total_alunos = models.PositiveIntegerField("total de alunos", default=0)
    total_turmas = models.PositiveIntegerField("total de turmas", default=0)
    pendencias = models.JSONField("pendências", default=list, blank=True)
    payload = models.JSONField("payload", default=dict, blank=True)

    class Meta:
        verbose_name = "exportação do censo"
        verbose_name_plural = "exportações do censo"
        ordering = ["-ano", "-versao"]
        constraints = [
            models.UniqueConstraint(
                fields=["escola", "ano", "versao"], name="exportacao_unica_por_escola_ano_versao"
            )
        ]

    def __str__(self) -> str:
        return f"Censo {self.ano} · {self.escola} · v{self.versao}"
