"""Usuário do sistema e perfis de acesso.

Substitui `pmieducar.usuario` + `pmieducar.tipo_usuario` do i-Educar original
por um usuário único com perfil e vínculo opcional a uma escola.
"""
from __future__ import annotations

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import EmailValidator
from django.db import models
from django.utils import timezone


class PerfilUsuario(models.TextChoices):
    ADMINISTRADOR = "administrador", "Administrador"
    GESTOR = "gestor", "Gestor escolar"
    SECRETARIA = "secretaria", "Secretaria escolar"
    PROFESSOR = "professor", "Professor"
    CONSULTA = "consulta", "Consulta"


class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def _criar(self, email: str, password: str | None, **extra):
        if not email:
            raise ValueError("O e-mail é obrigatório.")
        email = self.normalize_email(email).lower()
        usuario = self.model(email=email, **extra)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_user(self, email: str, password: str | None = None, **extra):
        extra.setdefault("perfil", PerfilUsuario.CONSULTA)
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._criar(email, password, **extra)

    def create_superuser(self, email: str, password: str | None = None, **extra):
        extra.setdefault("perfil", PerfilUsuario.ADMINISTRADOR)
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        if extra.get("is_staff") is not True or extra.get("is_superuser") is not True:
            raise ValueError("Superusuário precisa de is_staff e is_superuser verdadeiros.")
        return self._criar(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        "e-mail", unique=True, validators=[EmailValidator(message="Informe um e-mail válido.")]
    )
    nome_completo = models.CharField("nome completo", max_length=150)
    perfil = models.CharField(
        "perfil", max_length=20, choices=PerfilUsuario.choices, default=PerfilUsuario.CONSULTA
    )
    escola = models.ForeignKey(
        "schools.Escola",
        verbose_name="escola",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="usuarios",
        help_text="Preenchido para usuários lotados em uma escola específica.",
    )
    aluno = models.OneToOneField(
        "people.Aluno",
        verbose_name="aluno",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="usuario",
        help_text="Vincula o login do aluno/responsável ao cadastro do aluno.",
    )
    servidor = models.OneToOneField(
        "people.Servidor",
        verbose_name="servidor",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="usuario",
        help_text="Vincula o login ao cadastro funcional (para professores).",
    )
    is_active = models.BooleanField("ativo", default=True)
    is_staff = models.BooleanField("acesso ao admin", default=False)
    criado_em = models.DateTimeField("criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("atualizado em", auto_now=True)
    ultimo_acesso = models.DateTimeField("último acesso", null=True, blank=True)

    objects = UsuarioManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nome_completo"]

    class Meta:
        verbose_name = "usuário"
        verbose_name_plural = "usuários"
        ordering = ["nome_completo"]

    def __str__(self) -> str:
        return f"{self.nome_completo} <{self.email}>"

    def registrar_acesso(self) -> None:
        self.ultimo_acesso = timezone.now()
        self.save(update_fields=["ultimo_acesso"])
