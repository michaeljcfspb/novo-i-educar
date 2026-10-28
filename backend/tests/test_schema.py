import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_openapi_gerado(api):
    resposta = api.get("/api/schema/", HTTP_ACCEPT="application/json")
    assert resposta.status_code == 200
    schema = resposta.json()
    assert schema["info"]["title"] == "i-Educar API"
    for caminho in ("/api/v1/alunos/", "/api/v1/matriculas/", "/api/v1/auth/login/"):
        assert caminho in schema["paths"]


def test_swagger_disponivel(api):
    resposta = api.get("/api/docs/")
    assert resposta.status_code == 200
