"""Frequência diária do aluno na turma."""
from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import RegistroAuditavel


class Frequencia(RegistroAuditavel):
    matricula = models.ForeignKey(
        "enrollments.Matricula", verbose_name="matrícula", on_delete=models.CASCADE, related_name="frequencias"
    )
    turma = models.ForeignKey(
        "schools.Turma", verbose_name="turma", on_delete=models.CASCADE, related_name="frequencias"
    )
    data = models.DateField("data")
    presente = models.BooleanField("presente", default=True)
    justificativa = models.CharField("justificativa", max_length=200, blank=True)

    class Meta:
        verbose_name = "frequência"
        verbose_name_plural = "frequências"
        ordering = ["-data"]
        constraints = [
            models.UniqueConstraint(fields=["matricula", "data"], name="frequencia_unica_por_matricula_dia")
        ]
        indexes = [models.Index(fields=["turma", "data"])]

    def __str__(self) -> str:
        return f"{self.matricula} {self.data} {'P' if self.presente else 'F'}"

    def clean(self):
        if self.turma_id and self.matricula_id and self.turma.escola_id != self.matricula.escola_id:
            raise ValidationError({"turma": "A turma pertence a outra escola."})
