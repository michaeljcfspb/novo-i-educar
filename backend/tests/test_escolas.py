import pytest

pytestmark = pytest.mark.django_db


def test_cria_escola(autenticado, instituicao):
    resposta = autenticado.post(
        "/api/v1/escolas/",
        {"instituicao": instituicao.id, "nome": "Escola Nova", "sigla": "ENOVA"},
        format="json",
    )
    assert resposta.status_code == 201, resposta.data


def test_sigla_de_escola_unica(autenticado, escola, instituicao):
    resposta = autenticado.post(
        "/api/v1/escolas/",
        {"instituicao": instituicao.id, "nome": "Outra", "sigla": escola.sigla},
        format="json",
    )
    assert resposta.status_code == 400


def test_valida_idade_da_serie(autenticado, curso):
    resposta = autenticado.post(
        "/api/v1/series/",
        {"curso": curso.id, "nome": "2º Ano", "etapa": 2, "idade_inicial": 8, "idade_final": 7},
        format="json",
    )
    assert resposta.status_code == 400
    assert "idade_final" in resposta.data


def test_turma_ano_obrigatorio(autenticado, escola, serie):
    resposta = autenticado.post(
        "/api/v1/turmas/",
        {"escola": escola.id, "serie": serie.id, "nome": "Turma sem ano"},
        format="json",
    )
    assert resposta.status_code == 400
    assert "ano" in resposta.data


def test_filtra_turmas_por_ano(autenticado, turma):
    assert autenticado.get("/api/v1/turmas/?ano=2026").data["count"] == 1
    assert autenticado.get("/api/v1/turmas/?ano=2025").data["count"] == 0
