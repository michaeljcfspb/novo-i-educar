"""Matrícula e enturmação.

Equivale a `pmieducar.matricula` + `pmieducar.matricula_turma`, com as regras de
negócio que no sistema legado ficavam espalhadas em controllers.
"""
from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.core.models import RegistroAuditavel
from apps.people.models import Aluno
from apps.schools.models import Curso, Escola, Serie, Turma


class SituacaoMatricula(models.TextChoices):
    CURSANDO = "cursando", "Cursando"
    APROVADO = "aprovado", "Aprovado"
    REPROVADO = "reprovado", "Reprovado"
    TRANSFERIDO = "transferido", "Transferido"
    ABANDONOU = "abandonou", "Abandonou"
    FALECIDO = "falecido", "Falecido"
    CANCELADA = "cancelada", "Cancelada"


class Matricula(RegistroAuditavel):
    aluno = models.ForeignKey(
        Aluno, verbose_name="aluno", on_delete=models.PROTECT, related_name="matriculas"
    )
    escola = models.ForeignKey(
        Escola, verbose_name="escola", on_delete=models.PROTECT, related_name="matriculas"
    )
    serie = models.ForeignKey(
        Serie, verbose_name="série", on_delete=models.PROTECT, related_name="matriculas"
    )
    curso = models.ForeignKey(
        Curso, verbose_name="curso", on_delete=models.PROTECT, related_name="matriculas"
    )
    ano = models.PositiveSmallIntegerField("ano letivo")
    data_matricula = models.DateField("data da matrícula")
    situacao = models.CharField(
        "situação", max_length=15, choices=SituacaoMatricula.choices, default=SituacaoMatricula.CURSANDO
    )
    ativo = models.BooleanField("ativa", default=True)
    observacao = models.TextField("observação", blank=True)

    class Meta:
        verbose_name = "matrícula"
        verbose_name_plural = "matrículas"
        ordering = ["-ano", "aluno__pessoa__nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["aluno", "ano"],
                condition=Q(ativo=True),
                name="matricula_ativa_unica_por_aluno_ano",
            )
        ]
        indexes = [models.Index(fields=["ano", "escola"]), models.Index(fields=["situacao"])]

    def __str__(self) -> str:
        return f"{self.aluno} — {self.ano}"

    def clean(self):
        if self.serie_id and self.curso_id and self.serie.curso_id != self.curso_id:
            raise ValidationError({"curso": "O curso deve ser o mesmo da série selecionada."})

    def save(self, *args, **kwargs):
        if self.serie_id and not self.curso_id:
            self.curso_id = self.serie.curso_id
        super().save(*args, **kwargs)


class MatriculaTurma(RegistroAuditavel):
    matricula = models.ForeignKey(
        Matricula, verbose_name="matrícula", on_delete=models.CASCADE, related_name="enturmacoes"
    )
    turma = models.ForeignKey(
        Turma, verbose_name="turma", on_delete=models.PROTECT, related_name="matriculas"
    )
    data_enturmacao = models.DateField("data de enturmação")
    ativo = models.BooleanField("ativa", default=True)
    sequencial = models.PositiveSmallIntegerField("sequencial", default=1)

    class Meta:
        verbose_name = "enturmação"
        verbose_name_plural = "enturmações"
        ordering = ["-data_enturmacao"]
        constraints = [
            models.UniqueConstraint(
                fields=["matricula"],
                condition=Q(ativo=True),
                name="enturmacao_ativa_unica_por_matricula",
            )
        ]

    def __str__(self) -> str:
        return f"{self.matricula} → {self.turma}"

    def clean(self):
        if not self.turma_id or not self.matricula_id:
            return
        if self.turma.escola_id != self.matricula.escola_id:
            raise ValidationError({"turma": "A turma pertence a outra escola."})
        if self.turma.ano != self.matricula.ano:
            raise ValidationError({"turma": "O ano da turma difere do ano da matrícula."})
        if self.turma.serie_id != self.matricula.serie_id:
            raise ValidationError({"turma": "A turma pertence a outra série."})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
