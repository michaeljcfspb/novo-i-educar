import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User

pytestmark = pytest.mark.django_db


def test_login_retorna_usuario_e_cria_sessao(api, admin_user):
    resposta = api.post(
        "/api/v1/auth/login/",
        {"email": "admin@example.com", "password": "senha-forte-123"},
        format="json",
    )
    assert resposta.status_code == 200
    assert resposta.data["email"] == "admin@example.com"
    assert resposta.data["perfil"] == "administrador"
    assert api.session.get("_auth_user_id") == str(admin_user.pk)


def test_login_senha_invalida(api, admin_user):
    resposta = api.post(
        "/api/v1/auth/login/",
        {"email": "admin@example.com", "password": "errada"},
        format="json",
    )
    assert resposta.status_code == 400
    assert "detail" in resposta.data


def test_login_usuario_inativo(api, admin_user):
    admin_user.is_active = False
    admin_user.save()
    resposta = api.post(
        "/api/v1/auth/login/",
        {"email": "admin@example.com", "password": "senha-forte-123"},
        format="json",
    )
    assert resposta.status_code == 400


def test_me_exige_autenticacao(api):
    resposta = api.get("/api/v1/auth/me/")
    assert resposta.status_code in (401, 403)


def test_me_retorna_dados_do_usuario(autenticado, admin_user):
    resposta = autenticado.get("/api/v1/auth/me/")
    assert resposta.status_code == 200
    assert resposta.data["nome_completo"] == "Admin"


def test_logout_encerra_sessao(api, admin_user):
    api.post(
        "/api/v1/auth/login/",
        {"email": "admin@example.com", "password": "senha-forte-123"},
        format="json",
    )
    assert api.post("/api/v1/auth/logout/").status_code == 204
    assert api.get("/api/v1/auth/me/").status_code in (401, 403)


def test_token_autentica_requisicoes(api, admin_user):
    resposta = api.post(
        "/api/v1/auth/token/",
        {"email": "admin@example.com", "password": "senha-forte-123"},
        format="json",
    )
    assert resposta.status_code == 200
    token = resposta.data["token"]

    cliente = APIClient()
    cliente.credentials(HTTP_AUTHORIZATION=f"Token {token}")
    assert cliente.get("/api/v1/auth/me/").status_code == 200


def test_csrf_cookie_e_exigido_no_login_com_csrf(admin_user):
    cliente = APIClient(enforce_csrf_checks=True)
    # Sem token CSRF o login deve ser bloqueado.
    resposta = cliente.post(
        "/api/v1/auth/login/",
        {"email": "admin@example.com", "password": "senha-forte-123"},
        format="json",
    )
    assert resposta.status_code == 403

    cliente.get("/api/v1/auth/csrf/")
    csrf = cliente.cookies["csrftoken"].value
    resposta = cliente.post(
        "/api/v1/auth/login/",
        {"email": "admin@example.com", "password": "senha-forte-123"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf,
    )
    assert resposta.status_code == 200


def test_healthcheck_publico(api):
    resposta = api.get("/api/v1/health/")
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "ok"
