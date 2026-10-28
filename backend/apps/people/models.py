"""Pessoas (físicas/jurídicas) e alunos.

Corresponde a `cadastro.pessoa` + `cadastro.fisica` + `pmieducar.aluno` do
sistema legado, normalizados em modelos Django.
"""
from __future__ import annotations

from django.core.validators import MinLengthValidator
from django.db import models

from apps.core.models import RegistroAuditavel, Municipio
from .validators import validar_cep, validar_cpf


class TipoPessoa(models.TextChoices):
    FISICA = "fisica", "Pessoa física"
    JURIDICA = "juridica", "Pessoa jurídica"


class Sexo(models.TextChoices):
    MASCULINO = "M", "Masculino"
    FEMININO = "F", "Feminino"
    NAO_INFORMADO = "NI", "Não informado"


class Deficiencia(RegistroAuditavel):
    nome = models.CharField("nome", max_length=100, unique=True)
    codigo_censo = models.CharField("código do censo", max_length=10, blank=True)

    class Meta:
        verbose_name = "deficiência"
        verbose_name_plural = "deficiências"
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome


class Pessoa(RegistroAuditavel):
    tipo = models.CharField(
        "tipo", max_length=10, choices=TipoPessoa.choices, default=TipoPessoa.FISICA
    )
    nome = models.CharField("nome", max_length=200)
    nome_social = models.CharField("nome social", max_length=200, blank=True)
    cpf = models.CharField(
        "CPF",
        max_length=14,
        blank=True,
        null=True,
        unique=True,
        validators=[validar_cpf],
        help_text="Formato 000.000.000-00 ou apenas dígitos.",
    )
    cnpj = models.CharField("CNPJ", max_length=18, blank=True, null=True, unique=True)
    data_nascimento = models.DateField("data de nascimento", null=True, blank=True)
    sexo = models.CharField("sexo", max_length=2, choices=Sexo.choices, blank=True)
    email = models.EmailField("e-mail", blank=True)
    telefone = models.CharField("telefone", max_length=20, blank=True)
    nome_mae = models.CharField("nome da mãe", max_length=200, blank=True)
    nome_pai = models.CharField("nome do pai", max_length=200, blank=True)
    nacionalidade = models.CharField("nacionalidade", max_length=100, blank=True, default="Brasileira")
    cep = models.CharField("CEP", max_length=9, blank=True, validators=[validar_cep])
    logradouro = models.CharField("logradouro", max_length=200, blank=True)
    numero = models.CharField("número", max_length=20, blank=True)
    complemento = models.CharField("complemento", max_length=100, blank=True)
    bairro = models.CharField("bairro", max_length=100, blank=True)
    municipio = models.ForeignKey(
        Municipio,
        verbose_name="município",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="pessoas",
    )
    ativo = models.BooleanField("ativo", default=True)

    class Meta:
        verbose_name = "pessoa"
        verbose_name_plural = "pessoas"
        ordering = ["nome"]
        indexes = [models.Index(fields=["nome"]), models.Index(fields=["cpf"])]

    def __str__(self) -> str:
        return self.nome

    def save(self, *args, **kwargs):
        if self.cpf:
            self.cpf = self.cpf.replace(".", "").replace("-", "").strip() or None
        if self.email:
            self.email = self.email.lower().strip()
        super().save(*args, **kwargs)


class Aluno(RegistroAuditavel):
    pessoa = models.OneToOneField(
        Pessoa, verbose_name="pessoa", on_delete=models.PROTECT, related_name="aluno"
    )
    codigo = models.CharField("código do aluno", max_length=20, unique=True, blank=True)
    codigo_inep = models.CharField(
        "código INEP", max_length=12, blank=True, help_text="Código do aluno no Censo Escolar."
    )
    ativo = models.BooleanField("ativo", default=True)
    foto = models.ImageField("foto", upload_to="alunos/fotos/", null=True, blank=True)
    deficiencias = models.ManyToManyField(
        Deficiencia, verbose_name="deficiências", blank=True, related_name="alunos"
    )
    usa_transporte_escolar = models.BooleanField("usa transporte escolar", default=False)
    recebe_escolarizacao_outro_espaco = models.BooleanField(
        "recebe escolarização em outro espaço", default=False
    )
    observacoes = models.TextField("observações", blank=True)

    class Meta:
        verbose_name = "aluno"
        verbose_name_plural = "alunos"
        ordering = ["pessoa__nome"]

    def __str__(self) -> str:
        return f"{self.pessoa.nome} ({self.codigo})"

    def save(self, *args, **kwargs):
        criando = self._state.adding
        super().save(*args, **kwargs)
        if criando and not self.codigo:
            self.codigo = f"A{self.pk:06d}"
            super().save(update_fields=["codigo"])


class CargoServidor(models.TextChoices):
    PROFESSOR = "professor", "Professor"
    PEDAGOGO = "pedagogo", "Pedagogo"
    DIRETOR = "diretor", "Diretor"
    SECRETARIO_ESCOLAR = "secretario_escolar", "Secretário escolar"
    AUXILIAR = "auxiliar", "Auxiliar"
    OUTRO = "outro", "Outro"


class Servidor(RegistroAuditavel):
    """Servidor lotado em uma escola (professor, diretor, secretaria...).

    Substitui `pmieducar.servidor` + `pmieducar.funcionario` do legado.
    """

    pessoa = models.OneToOneField(
        Pessoa, verbose_name="pessoa", on_delete=models.PROTECT, related_name="servidor"
    )
    matricula_funcional = models.CharField(
        "matrícula funcional", max_length=30, unique=True, blank=True
    )
    cargo = models.CharField(
        "cargo", max_length=25, choices=CargoServidor.choices, default=CargoServidor.PROFESSOR
    )
    escola = models.ForeignKey(
        "schools.Escola",
        verbose_name="escola de lotação",
        on_delete=models.PROTECT,
        related_name="servidores",
    )
    disciplinas = models.ManyToManyField(
        "schools.Disciplina", verbose_name="disciplinas", blank=True, related_name="servidores"
    )
    data_admissao = models.DateField("data de admissão", null=True, blank=True)
    ativo = models.BooleanField("ativo", default=True)

    class Meta:
        verbose_name = "servidor"
        verbose_name_plural = "servidores"
        ordering = ["pessoa__nome"]

    def __str__(self) -> str:
        return f"{self.pessoa.nome} ({self.get_cargo_display()})"

    def save(self, *args, **kwargs):
        criando = self._state.adding
        super().save(*args, **kwargs)
        if criando and not self.matricula_funcional:
            self.matricula_funcional = f"S{self.pk:06d}"
            super().save(update_fields=["matricula_funcional"])
