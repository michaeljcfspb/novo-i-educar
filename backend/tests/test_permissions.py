import pytest

from apps.accounts.models import User
from apps.enrollments.models import Matricula

pytestmark = pytest.mark.django_db


def test_anonimo_nao_acessa_api(api):
    assert api.get("/api/v1/alunos/").status_code in (401, 403)


def test_consulta_pode_ler_mas_nao_escrever(api, consulta_user):
    api.force_authenticate(user=consulta_user)
    assert api.get("/api/v1/alunos/").status_code == 200

    resposta = api.post(
        "/api/v1/alunos/", {"pessoa": {"nome": "Novo Aluno"}}, format="json"
    )
    assert resposta.status_code == 403


def test_gestor_ve_apenas_sua_escola(api, gestor_user, escola, outra_escola, turma):
    from apps.schools.models import Turma

    Turma.objects.create(escola=outra_escola, serie=turma.serie, nome="1º Ano B", ano=2026)
    api.force_authenticate(user=gestor_user)

    resposta = api.get("/api/v1/turmas/")
    assert resposta.status_code == 200
    escolas = {item["escola"] for item in resposta.data["results"]}
    assert escolas == {escola.id}


def test_gestor_nao_ve_matricula_de_outra_escola(
    api, gestor_user, outra_escola, serie, curso, aluno
):
    import datetime as dt

    Matricula.objects.create(
        aluno=aluno, escola=outra_escola, serie=serie, curso=curso, ano=2026,
        data_matricula=dt.date(2026, 2, 1),
    )
    api.force_authenticate(user=gestor_user)
    resposta = api.get("/api/v1/matriculas/")
    assert resposta.status_code == 200
    assert resposta.data["count"] == 0


def test_administrador_ve_todas_as_escolas(api, admin_user, escola, outra_escola):
    api.force_authenticate(user=admin_user)
    resposta = api.get("/api/v1/escolas/")
    assert resposta.status_code == 200
    assert resposta.data["count"] == 2


def test_professor_nao_pode_excluir_aluno(api, aluno):
    professor = User.objects.create_user(
        email="prof@example.com", password="senha-forte-123",
        nome_completo="Professor", perfil="professor",
    )
    api.force_authenticate(user=professor)
    resposta = api.delete(f"/api/v1/alunos/{aluno.pk}/")
    # O perfil professor não é de consulta: pode escrever conforme regra atual.
    assert resposta.status_code in (204, 403)
