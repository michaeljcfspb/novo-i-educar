"""Histórico escolar, transferências e documentos emitidos.

Equivale a `pmieducar.historico_escolar`, `pmieducar.historico_disciplinas` e às
solicitações de transferência do legado.
"""
from __future__ import annotations

from decimal import Decimal

from django.core.validators import MaxValueValidator
from django.db import models

from apps.core.models import RegistroAuditavel


class SituacaoHistorico(models.TextChoices):
    EM_CURSO = "em_curso", "Em curso"
    APROVADO = "aprovado", "Aprovado"
    REPROVADO = "reprovado", "Reprovado"
    TRANSFERIDO = "transferido", "Transferido"
    ABANDONOU = "abandonou", "Abandonou"


class HistoricoEscolar(RegistroAuditavel):
    """Retrato do percurso do aluno em um ano/série."""

    aluno = models.ForeignKey(
        "people.Aluno", verbose_name="aluno", on_delete=models.CASCADE, related_name="historicos"
    )
    matricula = models.ForeignKey(
        "enrollments.Matricula",
        verbose_name="matrícula",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="historicos",
    )
    escola = models.ForeignKey(
        "schools.Escola", verbose_name="escola", on_delete=models.PROTECT, related_name="historicos"
    )
    serie = models.ForeignKey(
        "schools.Serie", verbose_name="série", on_delete=models.PROTECT, related_name="historicos"
    )
    ano = models.PositiveSmallIntegerField("ano letivo")
    carga_horaria_total = models.PositiveIntegerField("carga horária total (h)", default=0)
    dias_letivos = models.PositiveIntegerField("dias letivos", default=0)
    frequencia_percentual = models.DecimalField(
        "frequência (%)", max_digits=5, decimal_places=2, default=Decimal("0"),
        validators=[MaxValueValidator(100)],
    )
    media_geral = models.DecimalField(
        "média geral", max_digits=5, decimal_places=2, default=Decimal("0")
    )
    situacao = models.CharField(
        "situação", max_length=15, choices=SituacaoHistorico.choices, default=SituacaoHistorico.EM_CURSO
    )
    observacoes = models.TextField("observações", blank=True)

    class Meta:
        verbose_name = "histórico escolar"
        verbose_name_plural = "históricos escolares"
        ordering = ["-ano", "aluno__pessoa__nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["aluno", "ano", "serie"], name="historico_unico_por_aluno_ano_serie"
            )
        ]

    def __str__(self) -> str:
        return f"{self.aluno} · {self.ano} · {self.serie}"


class HistoricoDisciplina(RegistroAuditavel):
    historico = models.ForeignKey(
        HistoricoEscolar, verbose_name="histórico", on_delete=models.CASCADE, related_name="disciplinas"
    )
    disciplina = models.ForeignKey(
        "schools.Disciplina", verbose_name="disciplina", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="historicos",
    )
    nome_disciplina = models.CharField("nome da disciplina", max_length=150)
    carga_horaria = models.PositiveIntegerField("carga horária (h)", default=0)
    media = models.DecimalField("média", max_digits=5, decimal_places=2, default=Decimal("0"))
    frequencia = models.DecimalField(
        "frequência (%)", max_digits=5, decimal_places=2, default=Decimal("0")
    )
    situacao = models.CharField(
        "situação", max_length=15, choices=SituacaoHistorico.choices, default=SituacaoHistorico.EM_CURSO
    )

    class Meta:
        verbose_name = "disciplina do histórico"
        verbose_name_plural = "disciplinas do histórico"
        ordering = ["nome_disciplina"]

    def __str__(self) -> str:
        return f"{self.nome_disciplina}: {self.media}"


class TipoTransferencia(models.TextChoices):
    ENTRADA = "entrada", "Entrada"
    SAIDA = "saida", "Saída"
    INTERNA = "interna", "Interna (troca de escola/turma)"


class MotivoTransferencia(models.TextChoices):
    MUDANCA_ENDERECO = "mudanca_endereco", "Mudança de endereço"
    PEDIDO_RESPONSAVEL = "pedido_responsavel", "Pedido do responsável"
    SAUDE = "saude", "Motivo de saúde"
    TRANSFERENCIA_ESCOLA = "transferencia_escola", "Transferência de escola"
    OUTRO = "outro", "Outro"


class Transferencia(RegistroAuditavel):
    matricula = models.ForeignKey(
        "enrollments.Matricula",
        verbose_name="matrícula",
        on_delete=models.CASCADE,
        related_name="transferencias",
    )
    tipo = models.CharField("tipo", max_length=10, choices=TipoTransferencia.choices)
    data = models.DateField("data")
    escola_origem = models.ForeignKey(
        "schools.Escola", verbose_name="escola de origem", null=True, blank=True,
        on_delete=models.PROTECT, related_name="transferencias_saida",
    )
    escola_destino = models.ForeignKey(
        "schools.Escola", verbose_name="escola de destino", null=True, blank=True,
        on_delete=models.PROTECT, related_name="transferencias_entrada",
    )
    motivo = models.CharField(
        "motivo", max_length=25, choices=MotivoTransferencia.choices,
        default=MotivoTransferencia.PEDIDO_RESPONSAVEL,
    )
    observacao = models.TextField("observação", blank=True)

    class Meta:
        verbose_name = "transferência"
        verbose_name_plural = "transferências"
        ordering = ["-data"]

    def __str__(self) -> str:
        return f"{self.get_tipo_display()} · {self.matricula} · {self.data}"


class TipoDocumento(models.TextChoices):
    DECLARACAO_MATRICULA = "declaracao_matricula", "Declaração de matrícula"
    DECLARACAO_FREQUENCIA = "declaracao_frequencia", "Declaração de frequência"
    DECLARACAO_CONCLUSAO = "declaracao_conclusao", "Declaração de conclusão"
    HISTORICO_ESCOLAR = "historico_escolar", "Histórico escolar"
    TRANSFERENCIA = "transferencia", "Guia de transferência"


class Documento(RegistroAuditavel):
    aluno = models.ForeignKey(
        "people.Aluno", verbose_name="aluno", on_delete=models.CASCADE, related_name="documentos"
    )
    matricula = models.ForeignKey(
        "enrollments.Matricula", verbose_name="matrícula", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="documentos",
    )
    tipo = models.CharField("tipo", max_length=25, choices=TipoDocumento.choices)
    numero = models.CharField("número", max_length=30, unique=True, blank=True)
    titulo = models.CharField("título", max_length=150)
    corpo = models.TextField("corpo")
    emitido_em = models.DateTimeField("emitido em", auto_now_add=True)

    class Meta:
        verbose_name = "documento"
        verbose_name_plural = "documentos"
        ordering = ["-emitido_em"]

    def __str__(self) -> str:
        return f"{self.numero} · {self.get_tipo_display()}"

    def save(self, *args, **kwargs):
        criando = self._state.adding
        super().save(*args, **kwargs)
        if criando and not self.numero:
            self.numero = f"DOC-{self.emitido_em.year}-{self.pk:06d}"
            super().save(update_fields=["numero"])
