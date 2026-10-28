"""Servidor local: entrega o build do React (frontend/dist) pelo próprio Django.

Em produção (Docker/Easypanel) quem serve o SPA é o Nginx; este modo existe para
rodar tudo em um único processo local, sem precisar de Node nem Docker.
"""
from __future__ import annotations

import mimetypes
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET


def _dist() -> Path:
    return Path(settings.FRONTEND_DIST)


@require_GET
@ensure_csrf_cookie
def spa(request, caminho: str = ""):
    dist = _dist()
    indice = dist / "index.html"
    if not indice.exists():
        return HttpResponse(
            "Build do frontend não encontrado. Rode `npm run build` em frontend/.",
            status=503,
            content_type="text/plain; charset=utf-8",
        )

    if caminho:
        alvo = (dist / caminho).resolve()
        try:
            alvo.relative_to(dist.resolve())
        except ValueError:
            raise Http404("Caminho inválido.")
        if alvo.is_file():
            tipo, _ = mimetypes.guess_type(str(alvo))
            return FileResponse(alvo.open("rb"), content_type=tipo or "application/octet-stream")

    return FileResponse(indice.open("rb"), content_type="text/html; charset=utf-8")
