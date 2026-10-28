import pytest

from apps.schools.models import CalendarioDia

pytestmark = pytest.mark.django_db


def test_admin_cria_ano_letivo(autenticado, instituicao):
    resposta = autenticado.post(
        "/api/v1/anos-letivos/",
        {
            "instituicao": instituicao.id,
            "ano": 2027,
            "data_inicio": "2027-02-01",
            "data_fim": "2027-12-15",
        },
        format="json",
    )
    assert resposta.status_code == 201, resposta.data


def test_ano_letivo_duplicado(autenticado, ano_letivo):
    resposta = autenticado.post(
        "/api/v1/anos-letivos/",
        {
            "instituicao": ano_letivo.instituicao_id,
            "ano": ano_letivo.ano,
            "data_inicio": "2026-02-01",
            "data_fim": "2026-12-15",
        },
        format="json",
    )
    assert resposta.status_code == 400


def test_data_final_anterior_a_inicial(autenticado, instituicao):
    resposta = autenticado.post(
        "/api/v1/anos-letivos/",
        {
            "instituicao": instituicao.id,
            "ano": 2028,
            "data_inicio": "2028-06-01",
            "data_fim": "2028-02-01",
        },
        format="json",
    )
    assert resposta.status_code == 400
    assert "data_fim" in resposta.data


def test_gestor_nao_cria_ano_letivo(api, gestor_user, instituicao):
    api.force_authenticate(user=gestor_user)
    resposta = api.post(
        "/api/v1/anos-letivos/",
        {"instituicao": instituicao.id, "ano": 2029, "data_inicio": "2029-02-01", "data_fim": "2029-12-01"},
        format="json",
    )
    assert resposta.status_code == 403


def test_lanca_dias_do_calendario(autenticado, calendario):
    resposta = autenticado.post(
        f"/api/v1/calendarios/{calendario.pk}/dias/",
        [
            {"calendario": calendario.id, "data": "2026-03-02", "tipo": "letivo"},
            {"calendario": calendario.id, "data": "2026-03-03", "tipo": "feriado", "descricao": "Feriado"},
        ],
        format="json",
    )
    assert resposta.status_code == 201, resposta.data
    assert CalendarioDia.objects.filter(calendario=calendario).count() == 2

    dias = autenticado.get(f"/api/v1/calendarios/{calendario.pk}/dias/")
    assert len(dias.data) == 2
    detalhe = autenticado.get(f"/api/v1/calendarios/{calendario.pk}/")
    assert detalhe.data["dias_letivos"] == 1


def test_aloca_disciplina_na_turma(autenticado, turma, disciplina, servidor_professor):
    resposta = autenticado.post(
        "/api/v1/turma-disciplinas/",
        {
            "turma": turma.id,
            "disciplina": disciplina.id,
            "professor": servidor_professor.id,
            "carga_horaria": 200,
        },
        format="json",
    )
    assert resposta.status_code == 201, resposta.data


def test_professor_de_outra_escola_e_rejeitado(
    autenticado, turma, outra_escola, disciplina
):
    from apps.people.models import CargoServidor, Pessoa, Servidor
    from apps.schools.models import Disciplina

    pessoa = Pessoa.objects.create(nome="Professor Externo")
    externo = Servidor.objects.create(
        pessoa=pessoa, escola=outra_escola, cargo=CargoServidor.PROFESSOR
    )
    outra_disciplina = Disciplina.objects.create(
        instituicao=turma.escola.instituicao, nome="História", sigla="HIS"
    )
    resposta = autenticado.post(
        "/api/v1/turma-disciplinas/",
        {"turma": turma.id, "disciplina": outra_disciplina.id, "professor": externo.id},
        format="json",
    )
    assert resposta.status_code == 400
    assert "professor" in resposta.data
