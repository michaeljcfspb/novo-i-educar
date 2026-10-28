import pytest

from apps.people.models import Servidor

pytestmark = pytest.mark.django_db


def payload(escola, disciplina, cpf="39053344705"):
    return {
        "pessoa": {"nome": "Novo Professor", "cpf": cpf},
        "escola": escola.id,
        "cargo": "professor",
        "disciplinas": [disciplina.id],
    }


def test_admin_cria_servidor(autenticado, escola, disciplina):
    resposta = autenticado.post("/api/v1/servidores/", payload(escola, disciplina), format="json")
    assert resposta.status_code == 201, resposta.data
    assert resposta.data["matricula_funcional"].startswith("S")
    assert resposta.data["disciplinas"] == [disciplina.id]


def test_gestor_nao_cria_servidor(api, gestor_user, escola, disciplina):
    api.force_authenticate(user=gestor_user)
    resposta = api.post("/api/v1/servidores/", payload(escola, disciplina), format="json")
    assert resposta.status_code == 403


def test_gestor_ve_apenas_servidores_da_sua_escola(
    api, gestor_user, escola, outra_escola, disciplina, servidor_professor
):
    from apps.people.models import CargoServidor, Pessoa

    outra_pessoa = Pessoa.objects.create(nome="Professor Externo")
    Servidor.objects.create(pessoa=outra_pessoa, escola=outra_escola, cargo=CargoServidor.PROFESSOR)
    api.force_authenticate(user=gestor_user)

    resposta = api.get("/api/v1/servidores/")
    assert resposta.status_code == 200
    assert resposta.data["count"] == 1
    assert resposta.data["results"][0]["escola"] == escola.id
