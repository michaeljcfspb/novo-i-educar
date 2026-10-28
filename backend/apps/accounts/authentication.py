"""Autenticação com CSRF obrigatório também para visitantes.

O `SessionAuthentication` do DRF só valida o CSRF quando já existe usuário na
sessão. Como o login é justamente o momento em que a sessão é criada, ele
precisa de uma checagem explícita para impedir *login CSRF* (o atacante forçar
a vítima a autenticar-se na conta dele).
"""
from __future__ import annotations

from rest_framework.authentication import SessionAuthentication


class CsrfObrigatorio(SessionAuthentication):
    def authenticate(self, request):
        self.enforce_csrf(request)
        return super().authenticate(request)
