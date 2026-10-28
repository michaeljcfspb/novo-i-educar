import datetime as dt

import pytest

from apps.enrollments.models import Matricula, SituacaoMatricula

pytestmark = pytest.mark.django_db


def payload_matricula(aluno, escola, serie, curso):
    return {
        "aluno": aluno.id,
        "escola": escola.id,
        "serie": serie.id,
        "curso": curso.id,
        "ano": 2026,
        "data_matricula": "2026-02-01",
    }


def test_cria_matricula(autenticado, aluno, escola, serie, curso):
    resposta = autenticado.post(
        "/api/v1/matriculas/", payload_matricula(aluno, escola, serie, curso), format="json"
    )
    assert resposta.status_code == 201, resposta.data
    assert resposta.data["situacao"] == "cursando"


def test_curso_incompativel_com_serie(autenticado, aluno, escola, serie, instituicao):
    from apps.schools.models import Curso

    outro = Curso.objects.create(
        instituicao=instituicao, nome="Ensino Médio", sigla="EM", nivel_ensino="medio"
    )
    resposta = autenticado.post(
        "/api/v1/matriculas/", payload_matricula(aluno, escola, serie, outro), format="json"
    )
    assert resposta.status_code == 400
    assert "curso" in str(resposta.data)


def test_nao_permite_duas_matriculas_ativas_no_mesmo_ano(
    autenticado, aluno, escola, serie, curso, matricula
):
    resposta = autenticado.post(
        "/api/v1/matriculas/", payload_matricula(aluno, escola, serie, curso), format="json"
    )
    assert resposta.status_code == 400


def test_enturma_matricula_na_turma(autenticado, matricula, turma):
    resposta = autenticado.post(
        f"/api/v1/matriculas/{matricula.pk}/enturmar/",
        {"turma": turma.id, "data_enturmacao": "2026-02-05"},
        format="json",
    )
    assert resposta.status_code == 201, resposta.data
    assert resposta.data["turma"] == turma.id


def test_enturmacao_respeita_capacidade(autenticado, matricula, turma, escola, serie, curso):
    from apps.people.models import Aluno, Pessoa

    for i in range(2):
        pessoa = Pessoa.objects.create(nome=f"Aluno {i}")
        aluno = Aluno.objects.create(pessoa=pessoa)
        m = Matricula.objects.create(
            aluno=aluno, escola=escola, serie=serie, curso=curso, ano=2026,
            data_matricula=dt.date(2026, 2, 1),
        )
        resposta = autenticado.post(
            f"/api/v1/matriculas/{m.pk}/enturmar/", {"turma": turma.id}, format="json"
        )
        assert resposta.status_code == 201, resposta.data

    resposta = autenticado.post(
        f"/api/v1/matriculas/{matricula.pk}/enturmar/", {"turma": turma.id}, format="json"
    )
    assert resposta.status_code == 400
    assert "vagas" in str(resposta.data).lower()


def test_enturmar_em_turma_de_outra_escola(
    autenticado, matricula, outra_escola, serie
):
    from apps.schools.models import Turma

    turma_externa = Turma.objects.create(
        escola=outra_escola, serie=serie, nome="1º Ano X", ano=2026
    )
    resposta = autenticado.post(
        f"/api/v1/matriculas/{matricula.pk}/enturmar/",
        {"turma": turma_externa.id},
        format="json",
    )
    assert resposta.status_code == 400


def test_altera_situacao(autenticado, matricula):
    resposta = autenticado.patch(
        f"/api/v1/matriculas/{matricula.pk}/situacao/",
        {"situacao": SituacaoMatricula.APROVADO},
        format="json",
    )
    assert resposta.status_code == 200
    assert resposta.data["situacao"] == "aprovado"


def test_cancelamento_e_logico(autenticado, matricula):
    resposta = autenticado.delete(f"/api/v1/matriculas/{matricula.pk}/")
    assert resposta.status_code == 204
    matricula.refresh_from_db()
    assert matricula.ativo is False
    assert matricula.situacao == "cancelada"
