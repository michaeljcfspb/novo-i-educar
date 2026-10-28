"""Permissões de domínio.

Regras herdadas do i-Educar original: administradores enxergam tudo; usuários
lotados em uma escola só enxergam os dados daquela escola; perfis de consulta
não escrevem.
"""
from __future__ import annotations

from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.accounts.models import PerfilUsuario


def eh_administrador(user) -> bool:
    return bool(
        user
        and user.is_authenticated
        and (user.is_superuser or getattr(user, "perfil", None) == PerfilUsuario.ADMINISTRADOR)
    )


class IsAdministrador(BasePermission):
    message = "Somente administradores podem executar esta ação."

    def has_permission(self, request, view) -> bool:
        return eh_administrador(request.user)


class IsGestorOuAdministrador(BasePermission):
    message = "Ação restrita a gestores e administradores."

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and (
                eh_administrador(request.user)
                or request.user.perfil
                in {PerfilUsuario.GESTOR, PerfilUsuario.SECRETARIA}
            )
        )


class SomenteLeituraParaConsulta(BasePermission):
    """Perfil CONSULTA só lê; os demais autenticados escrevem."""

    message = "Seu perfil permite apenas leitura."

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return getattr(user, "perfil", None) != PerfilUsuario.CONSULTA


def filtrar_por_escola(queryset, user, campo: str = "escola"):
    """Aplica o escopo de escola para usuários não administradores."""
    if eh_administrador(user) or getattr(user, "escola_id", None) is None:
        return queryset
    return queryset.filter(**{campo: user.escola_id})


def filtrar_por_escolas_relacionadas(queryset, user, caminho: str):
    """Escopo por escola quando a FK está a mais de um salto (ex.: matrícula)."""
    if eh_administrador(user) or getattr(user, "escola_id", None) is None:
        return queryset
    return queryset.filter(**{f"{caminho}__escola_id": user.escola_id})


class AdminEscreve(BasePermission):
    """Estrutura da rede (escolas, cursos, séries, calendário) só o admin altera."""

    message = "Somente administradores podem alterar a estrutura da rede."

    def has_permission(self, request, view) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return eh_administrador(request.user)


class EscopoPorEscolaEscrita(BasePermission):
    """Impede que um usuário escreva em registros de outra escola."""

    message = "Você só pode alterar registros da sua escola."

    def has_object_permission(self, request, view, obj) -> bool:
        if request.method in SAFE_METHODS:
            return True
        if eh_administrador(request.user) or getattr(request.user, "escola_id", None) is None:
            return True
        escola_id = getattr(obj, "escola_id", None)
        if escola_id is None and hasattr(obj, "matricula"):
            escola_id = obj.matricula.escola_id
        if escola_id is None and hasattr(obj, "turma"):
            escola_id = obj.turma.escola_id
        return escola_id == request.user.escola_id


def validar_escola_do_usuario(user, escola_id) -> None:
    """Valida, na escrita, que a escola informada pertence ao escopo do usuário."""
    from rest_framework.exceptions import PermissionDenied

    if eh_administrador(user) or getattr(user, "escola_id", None) is None:
        return
    if escola_id is not None and int(escola_id) != int(user.escola_id):
        raise PermissionDenied("Você só pode gravar dados da sua escola.")
