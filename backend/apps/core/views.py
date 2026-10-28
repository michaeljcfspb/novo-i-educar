from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView


@require_GET
def health(request):
    """Healthcheck usado por Docker/Easypanel (não exige autenticação)."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        banco = "ok"
    except Exception:  # pragma: no cover - depende da infraestrutura
        banco = "indisponivel"
    return JsonResponse(
        {"status": "ok" if banco == "ok" else "degradado", "banco": banco},
        status=200 if banco == "ok" else 503,
    )


class VersionView(APIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.Serializer

    @extend_schema(tags=["Cadastros"], summary="Versão da API", responses={200: OpenApiTypes.OBJECT})
    def get(self, request):
        return Response({"nome": "i-Educar API", "versao": "0.1.0"})
