"""Avaliação: períodos, regras, notas, recuperação e médias."""
from __future__ import annotations

from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

from apps.core.models import RegistroAuditavel


class TipoMedia(models.TextChoices):
    ARITMETICA = "aritmetica", "Média aritmética"
    PONDERADA = "ponderada", "Média ponderada"


class RegraAvaliacao(RegistroAuditavel):
    nome = models.CharField("nome", max_length=100, unique=True)
    tipo_media = models.CharField(
        "tipo de média", max_length=12, choices=TipoMedia.choices, default=TipoMedia.ARITMETICA
    )
    nota_maxima = models.DecimalField(
        "nota máxima", max_digits=5, decimal_places=2, default=Decimal("10.00"),
        validators=[MinValueValidator(Decimal("1")), MaxValueValidator(Decimal("1000"))],
    )
    media_aprovacao = models.DecimalField(
        "média de aprovação", max_digits=5, decimal_places=2, default=Decimal("6.00")
    )
    media_recuperacao = models.DecimalField(
        "média mínima após recuperação", max_digits=5, decimal_places=2, default=Decimal("5.00")
    )
    percentual_frequencia = models.PositiveSmallIntegerField(
        "frequência mínima (%)", default=75, validators=[MaxValueValidator(100)]
    )
    permite_recuperacao = models.BooleanField("permite recuperação", default=True)
    casas_decimais = models.PositiveSmallIntegerField(
        "casas decimais", default=1, validators=[MaxValueValidator(2)]
    )

    class Meta:
        verbose_name = "regra de avaliação"
        verbose_name_plural = "regras de avaliação"
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.media_recuperacao > self.media_aprovacao:
            raise ValidationError(
                {"media_recuperacao": "A média de recuperação não pode exceder a de aprovação."}
            )
        if self.nota_maxima < self.media_aprovacao:
            raise ValidationError({"nota_maxima": "A nota máxima deve ser maior que a média de aprovação."})


class PeriodoAvaliacao(RegistroAuditavel):
    ano_letivo = models.ForeignKey(
        "schools.AnoLetivo",
        verbose_name="ano letivo",
        on_delete=models.CASCADE,
        related_name="periodos",
    )
    nome = models.CharField("nome", max_length=60)
    ordem = models.PositiveSmallIntegerField("ordem")
    data_inicio = models.DateField("início")
    data_fim = models.DateField("término")
    peso = models.DecimalField("peso", max_digits=4, decimal_places=2, default=Decimal("1.00"))

    class Meta:
        verbose_name = "período de avaliação"
        verbose_name_plural = "períodos de avaliação"
        ordering = ["ano_letivo__ano", "ordem"]
        constraints = [
            models.UniqueConstraint(fields=["ano_letivo", "ordem"], name="periodo_unico_por_ano_letivo"),
            models.UniqueConstraint(fields=["ano_letivo", "nome"], name="periodo_nome_unico_por_ano_letivo"),
        ]

    def __str__(self) -> str:
        return f"{self.nome} ({self.ano_letivo.ano})"


class TipoNota(models.TextChoices):
    NORMAL = "normal", "Nota normal"
    RECUPERACAO = "recuperacao", "Recuperação"


class Nota(RegistroAuditavel):
    matricula = models.ForeignKey(
        "enrollments.Matricula", verbose_name="matrícula", on_delete=models.CASCADE, related_name="notas"
    )
    turma_disciplina = models.ForeignKey(
        "schools.TurmaDisciplina",
        verbose_name="disciplina da turma",
        on_delete=models.CASCADE,
        related_name="notas",
    )
    periodo = models.ForeignKey(
        PeriodoAvaliacao, verbose_name="período", on_delete=models.CASCADE, related_name="notas"
    )
    tipo = models.CharField("tipo", max_length=12, choices=TipoNota.choices, default=TipoNota.NORMAL)
    valor = models.DecimalField(
        "nota", max_digits=5, decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )
    observacao = models.CharField("observação", max_length=200, blank=True)

    class Meta:
        verbose_name = "nota"
        verbose_name_plural = "notas"
        ordering = ["matricula__aluno__pessoa__nome", "periodo__ordem"]
        constraints = [
            models.UniqueConstraint(
                fields=["matricula", "turma_disciplina", "periodo", "tipo"],
                name="nota_unica_por_matricula_disciplina_periodo_tipo",
            )
        ]
        indexes = [models.Index(fields=["turma_disciplina", "periodo"])]

    def __str__(self) -> str:
        return f"{self.matricula} · {self.turma_disciplina.disciplina} = {self.valor}"

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.turma_disciplina_id and self.matricula_id:
            if self.turma_disciplina.turma_id != self._turma_da_matricula():
                raise ValidationError({"turma_disciplina": "A disciplina não pertence à turma do aluno."})
        regra = self._regra()
        if regra and self.valor is not None and self.valor > regra.nota_maxima:
            raise ValidationError({"valor": f"A nota não pode exceder {regra.nota_maxima}."})

    def _turma_da_matricula(self):
        enturmacao = self.matricula.enturmacoes.filter(ativo=True).first()
        return enturmacao.turma_id if enturmacao else None

    def _regra(self) -> RegraAvaliacao | None:
        serie = self.matricula.serie if self.matricula_id else None
        return getattr(serie, "regra_avaliacao", None) if serie else None
