"""Formata erros da API com mensagens em português."""
from __future__ import annotations

from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.views import exception_handler

MENSAGENS = {
    status.HTTP_401_UNAUTHORIZED: "Autenticação necessária.",
    status.HTTP_403_FORBIDDEN: "Você não tem permissão para esta ação.",
    status.HTTP_404_NOT_FOUND: "Registro não encontrado.",
    status.HTTP_405_METHOD_NOT_ALLOWED: "Método não permitido.",
}


def tratador_de_excecoes(exc, context):
    resposta = exception_handler(exc, context)
    if resposta is None:
        return None

    if isinstance(exc, NotAuthenticated):
        resposta.data = {"detail": MENSAGENS[status.HTTP_401_UNAUTHORIZED]}
    elif isinstance(exc, PermissionDenied):
        resposta.data = {"detail": str(exc.detail) if str(exc.detail) else MENSAGENS[status.HTTP_403_FORBIDDEN]}
    elif resposta.status_code in MENSAGENS and isinstance(resposta.data, dict) and set(resposta.data) <= {"detail"}:
        resposta.data = {"detail": MENSAGENS[resposta.status_code]}
    return resposta
