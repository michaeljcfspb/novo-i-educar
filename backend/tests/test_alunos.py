import pytest

pytestmark = pytest.mark.django_db


def test_cria_aluno_com_pessoa_aninhada(autenticado, municipio, deficiencia):
    payload = {
        "pessoa": {
            "nome": "João Pedro Souza",
            "cpf": "11144477735",
            "data_nascimento": "2016-05-20",
            "sexo": "M",
            "municipio": municipio.id,
        },
        "deficiencias": [deficiencia.id],
        "usa_transporte_escolar": True,
    }
    resposta = autenticado.post("/api/v1/alunos/", payload, format="json")
    assert resposta.status_code == 201, resposta.data
    assert resposta.data["codigo"].startswith("A")
    assert resposta.data["pessoa"]["nome"] == "João Pedro Souza"
    assert resposta.data["deficiencias"] == [deficiencia.id]


def test_cpf_invalido_e_rejeitado(autenticado):
    payload = {"pessoa": {"nome": "Teste", "cpf": "12345678900"}}
    resposta = autenticado.post("/api/v1/alunos/", payload, format="json")
    assert resposta.status_code == 400
    assert "cpf" in str(resposta.data)


def test_cpf_duplicado_e_rejeitado(autenticado, aluno):
    payload = {"pessoa": {"nome": "Outra Pessoa", "cpf": aluno.pessoa.cpf}}
    resposta = autenticado.post("/api/v1/alunos/", payload, format="json")
    assert resposta.status_code == 400


def test_busca_por_nome(autenticado, aluno):
    resposta = autenticado.get("/api/v1/alunos/?search=Maria")
    assert resposta.status_code == 200
    assert resposta.data["count"] == 1


def test_atualiza_dados_da_pessoa(autenticado, aluno):
    resposta = autenticado.patch(
        f"/api/v1/alunos/{aluno.pk}/",
        {"pessoa": {"nome": "Maria da Silva Santos"}},
        format="json",
    )
    assert resposta.status_code == 200, resposta.data
    assert resposta.data["pessoa"]["nome"] == "Maria da Silva Santos"


def test_lista_matriculas_do_aluno(autenticado, aluno, matricula):
    resposta = autenticado.get(f"/api/v1/alunos/{aluno.pk}/matriculas/")
    assert resposta.status_code == 200
    assert len(resposta.data) == 1
