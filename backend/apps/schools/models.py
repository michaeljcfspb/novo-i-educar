"""Rede escolar: instituição, escola, curso, série, disciplina e turma.

Mapeia `pmieducar.instituicao`, `pmieducar.escola`, `pmieducar.curso`,
`pmieducar.serie`, `pmieducar.turma` e `modules.componente_curricular`.
"""
from __future__ import annotations

from django.db import models

from apps.core.models import Municipio, RegistroAuditavel
from apps.people.validators import validar_cep


class NivelEnsino(models.TextChoices):
    INFANTIL = "infantil", "Educação infantil"
    FUNDAMENTAL = "fundamental", "Ensino fundamental"
    MEDIO = "medio", "Ensino médio"
    EJA = "eja", "Educação de jovens e adultos"
    PROFISSIONAL = "profissional", "Educação profissional"
    SUPERIOR = "superior", "Ensino superior"


class Modalidade(models.TextChoices):
    PRESENCIAL = "presencial", "Presencial"
    EAD = "ead", "Educação a distância"
    HIBRIDO = "hibrido", "Híbrido"


class Turno(models.TextChoices):
    MATUTINO = "matutino", "Matutino"
    VESPERTINO = "vespertino", "Vespertino"
    NOTURNO = "noturno", "Noturno"
    INTEGRAL = "integral", "Integral"


class Instituicao(RegistroAuditavel):
    nome = models.CharField("nome", max_length=200)
    sigla = models.CharField("sigla", max_length=20, unique=True)
    cnpj = models.CharField("CNPJ", max_length=18, blank=True)
    email = models.EmailField("e-mail", blank=True)
    telefone = models.CharField("telefone", max_length=20, blank=True)
    municipio = models.ForeignKey(
        Municipio, verbose_name="município", null=True, blank=True, on_delete=models.PROTECT,
        related_name="instituicoes",
    )
    ativo = models.BooleanField("ativa", default=True)

    class Meta:
        verbose_name = "instituição"
        verbose_name_plural = "instituições"
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome


class Escola(RegistroAuditavel):
    instituicao = models.ForeignKey(
        Instituicao, verbose_name="instituição", on_delete=models.PROTECT, related_name="escolas"
    )
    nome = models.CharField("nome", max_length=200)
    sigla = models.CharField("sigla", max_length=50, unique=True)
    codigo_inep = models.CharField("código INEP", max_length=12, blank=True)
    email = models.EmailField("e-mail", blank=True)
    telefone = models.CharField("telefone", max_length=20, blank=True)
    cep = models.CharField("CEP", max_length=9, blank=True, validators=[validar_cep])
    logradouro = models.CharField("logradouro", max_length=200, blank=True)
    numero = models.CharField("número", max_length=20, blank=True)
    bairro = models.CharField("bairro", max_length=100, blank=True)
    municipio = models.ForeignKey(
        Municipio, verbose_name="município", null=True, blank=True, on_delete=models.PROTECT,
        related_name="escolas",
    )
    ativo = models.BooleanField("ativa", default=True)

    class Meta:
        verbose_name = "escola"
        verbose_name_plural = "escolas"
        ordering = ["nome"]
        indexes = [models.Index(fields=["nome"])]

    def __str__(self) -> str:
        return self.nome


class Curso(RegistroAuditavel):
    instituicao = models.ForeignKey(
        Instituicao, verbose_name="instituição", on_delete=models.PROTECT, related_name="cursos"
    )
    nome = models.CharField("nome", max_length=150)
    sigla = models.CharField("sigla", max_length=30)
    nivel_ensino = models.CharField("nível de ensino", max_length=20, choices=NivelEnsino.choices)
    modalidade = models.CharField(
        "modalidade", max_length=15, choices=Modalidade.choices, default=Modalidade.PRESENCIAL
    )
    carga_horaria = models.PositiveIntegerField("carga horária (h)", default=0)
    ativo = models.BooleanField("ativo", default=True)

    class Meta:
        verbose_name = "curso"
        verbose_name_plural = "cursos"
        ordering = ["nome"]
        constraints = [
            models.UniqueConstraint(fields=["instituicao", "nome"], name="curso_unico_por_instituicao")
        ]

    def __str__(self) -> str:
        return self.nome


class Serie(RegistroAuditavel):
    curso = models.ForeignKey(
        Curso, verbose_name="curso", on_delete=models.PROTECT, related_name="series"
    )
    nome = models.CharField("nome", max_length=100)
    etapa = models.PositiveSmallIntegerField("etapa", default=1)
    carga_horaria = models.PositiveIntegerField("carga horária (h)", default=0)
    regra_avaliacao = models.ForeignKey(
        "assessment.RegraAvaliacao",
        verbose_name="regra de avaliação",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="series",
    )
    idade_inicial = models.PositiveSmallIntegerField("idade inicial", default=0)
    idade_final = models.PositiveSmallIntegerField("idade final", default=0)
    ativo = models.BooleanField("ativa", default=True)

    class Meta:
        verbose_name = "série"
        verbose_name_plural = "séries"
        ordering = ["curso__nome", "etapa"]
        constraints = [
            models.UniqueConstraint(fields=["curso", "nome"], name="serie_unica_por_curso")
        ]

    def __str__(self) -> str:
        return f"{self.nome} — {self.curso.nome}"


class Disciplina(RegistroAuditavel):
    instituicao = models.ForeignKey(
        Instituicao, verbose_name="instituição", on_delete=models.PROTECT, related_name="disciplinas"
    )
    nome = models.CharField("nome", max_length=150)
    sigla = models.CharField("sigla", max_length=20, blank=True)
    area_conhecimento = models.CharField("área de conhecimento", max_length=100, blank=True)
    carga_horaria = models.PositiveIntegerField("carga horária (h)", default=0)
    ativo = models.BooleanField("ativa", default=True)

    class Meta:
        verbose_name = "disciplina"
        verbose_name_plural = "disciplinas"
        ordering = ["nome"]
        constraints = [
            models.UniqueConstraint(fields=["instituicao", "nome"], name="disciplina_unica_por_instituicao")
        ]

    def __str__(self) -> str:
        return self.nome


class Turma(RegistroAuditavel):
    escola = models.ForeignKey(
        Escola, verbose_name="escola", on_delete=models.PROTECT, related_name="turmas"
    )
    serie = models.ForeignKey(
        Serie, verbose_name="série", on_delete=models.PROTECT, related_name="turmas"
    )
    nome = models.CharField("nome", max_length=100)
    sigla = models.CharField("sigla", max_length=50, blank=True)
    codigo_inep = models.CharField(
        "código INEP", max_length=12, blank=True, help_text="Código da turma no Censo Escolar."
    )
    ano = models.PositiveSmallIntegerField("ano letivo")
    turno = models.CharField("turno", max_length=15, choices=Turno.choices, default=Turno.MATUTINO)
    capacidade = models.PositiveSmallIntegerField("capacidade", default=30)
    ativo = models.BooleanField("ativa", default=True)

    class Meta:
        verbose_name = "turma"
        verbose_name_plural = "turmas"
        ordering = ["-ano", "nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["escola", "nome", "ano"], name="turma_unica_por_escola_ano"
            )
        ]
        indexes = [models.Index(fields=["ano", "escola"])]

    def __str__(self) -> str:
        return f"{self.nome} ({self.ano})"

    @property
    def vagas_disponiveis(self) -> int:
        ocupadas = self.matriculas.filter(ativo=True).count()
        return max(self.capacidade - ocupadas, 0)


class AnoLetivo(RegistroAuditavel):
    instituicao = models.ForeignKey(
        Instituicao, verbose_name="instituição", on_delete=models.CASCADE, related_name="anos_letivos"
    )
    ano = models.PositiveSmallIntegerField("ano")
    data_inicio = models.DateField("início")
    data_fim = models.DateField("término")
    ativo = models.BooleanField("ativo", default=True)

    class Meta:
        verbose_name = "ano letivo"
        verbose_name_plural = "anos letivos"
        ordering = ["-ano"]
        constraints = [
            models.UniqueConstraint(fields=["instituicao", "ano"], name="ano_letivo_unico_por_instituicao")
        ]

    def __str__(self) -> str:
        return f"{self.ano} — {self.instituicao.sigla}"

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.data_inicio and self.data_fim and self.data_fim < self.data_inicio:
            raise ValidationError({"data_fim": "O término não pode ser anterior ao início."})


class TipoDiaCalendario(models.TextChoices):
    LETIVO = "letivo", "Dia letivo"
    FERIADO = "feriado", "Feriado"
    RECESSO = "recesso", "Recesso"
    EVENTO = "evento", "Evento"


class Calendario(RegistroAuditavel):
    ano_letivo = models.ForeignKey(
        AnoLetivo, verbose_name="ano letivo", on_delete=models.CASCADE, related_name="calendarios"
    )
    escola = models.ForeignKey(
        Escola,
        verbose_name="escola",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="calendarios",
        help_text="Vazio indica calendário da rede.",
    )
    nome = models.CharField("nome", max_length=100, default="Calendário escolar")
    ativo = models.BooleanField("ativo", default=True)

    class Meta:
        verbose_name = "calendário"
        verbose_name_plural = "calendários"
        ordering = ["ano_letivo__ano", "nome"]

    def __str__(self) -> str:
        return f"{self.nome} ({self.ano_letivo.ano})"

    @property
    def dias_letivos(self) -> int:
        return self.dias.filter(tipo=TipoDiaCalendario.LETIVO).count()


class CalendarioDia(RegistroAuditavel):
    calendario = models.ForeignKey(
        Calendario, verbose_name="calendário", on_delete=models.CASCADE, related_name="dias"
    )
    data = models.DateField("data")
    tipo = models.CharField(
        "tipo", max_length=10, choices=TipoDiaCalendario.choices, default=TipoDiaCalendario.LETIVO
    )
    descricao = models.CharField("descrição", max_length=200, blank=True)

    class Meta:
        verbose_name = "dia do calendário"
        verbose_name_plural = "dias do calendário"
        ordering = ["data"]
        constraints = [
            models.UniqueConstraint(fields=["calendario", "data"], name="dia_unico_por_calendario")
        ]

    def __str__(self) -> str:
        return f"{self.data} ({self.get_tipo_display()})"


class TurmaDisciplina(RegistroAuditavel):
    """Alocação de disciplina e professor em uma turma."""

    turma = models.ForeignKey(
        Turma, verbose_name="turma", on_delete=models.CASCADE, related_name="disciplinas"
    )
    disciplina = models.ForeignKey(
        Disciplina, verbose_name="disciplina", on_delete=models.PROTECT, related_name="turmas"
    )
    professor = models.ForeignKey(
        "people.Servidor",
        verbose_name="professor",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="alocacoes",
    )
    carga_horaria = models.PositiveIntegerField("carga horária (h)", default=0)

    class Meta:
        verbose_name = "disciplina da turma"
        verbose_name_plural = "disciplinas da turma"
        ordering = ["turma__nome", "disciplina__nome"]
        constraints = [
            models.UniqueConstraint(fields=["turma", "disciplina"], name="disciplina_unica_por_turma")
        ]

    def __str__(self) -> str:
        return f"{self.turma} · {self.disciplina}"
