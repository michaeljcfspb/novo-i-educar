"""Modelos base e cadastros geográficos."""
from __future__ import annotations

from django.conf import settings
from django.db import models


class RegistroAuditavel(models.Model):
    """Campos de auditoria comuns a todos os modelos de domínio."""

    # Liga a trilha de auditoria (apps/core/audit.py) no save/delete.
    auditar = True

    criado_em = models.DateTimeField("criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("atualizado em", auto_now=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="criado por",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        abstract = True


class Estado(RegistroAuditavel):
    nome = models.CharField("nome", max_length=100)
    sigla = models.CharField("sigla (UF)", max_length=2, unique=True)
    codigo_ibge = models.CharField("código IBGE", max_length=2, blank=True)

    class Meta:
        verbose_name = "estado"
        verbose_name_plural = "estados"
        ordering = ["nome"]

    def __str__(self) -> str:
        return f"{self.nome} ({self.sigla})"


class Municipio(RegistroAuditavel):
    nome = models.CharField("nome", max_length=150)
    estado = models.ForeignKey(
        Estado, verbose_name="estado", on_delete=models.PROTECT, related_name="municipios"
    )
    codigo_ibge = models.CharField("código IBGE", max_length=7, blank=True)

    class Meta:
        verbose_name = "município"
        verbose_name_plural = "municípios"
        ordering = ["nome"]
        constraints = [
            models.UniqueConstraint(fields=["nome", "estado"], name="municipio_unico_por_uf")
        ]

    def __str__(self) -> str:
        return f"{self.nome}/{self.estado.sigla}"


class RegistroAuditoria(models.Model):
    """Trilha de auditoria imutável das alterações de domínio."""

    class Acao(models.TextChoices):
        CRIADO = "criado", "Criado"
        ATUALIZADO = "atualizado", "Atualizado"
        EXCLUIDO = "excluido", "Excluído"

    entidade = models.CharField("entidade", max_length=100)
    objeto_id = models.CharField("id do objeto", max_length=50)
    acao = models.CharField("ação", max_length=15, choices=Acao.choices)
    dados = models.JSONField("dados", default=dict)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="usuário",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    criado_em = models.DateTimeField("criado em", auto_now_add=True)

    class Meta:
        verbose_name = "registro de auditoria"
        verbose_name_plural = "registros de auditoria"
        ordering = ["-criado_em"]
        indexes = [models.Index(fields=["entidade", "objeto_id"])]

    def __str__(self) -> str:
        return f"{self.entidade}#{self.objeto_id} {self.acao}"
