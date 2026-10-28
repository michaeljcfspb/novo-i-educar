import datetime as dt

import pytest

from apps.attendance.models import Frequencia

pytestmark = pytest.mark.django_db


def test_lote_cria_e_atualiza_chamada(autenticado, enturmado, turma):
    corpo = {
        "turma": turma.id,
        "data": "2026-03-10",
        "registros": [{"matricula": enturmado.matricula_id, "presente": False, "justificativa": "Atestado"}],
    }
    resposta = autenticado.post("/api/v1/frequencias/lote/", corpo, format="json")
    assert resposta.status_code == 201, resposta.data
    assert Frequencia.objects.filter(matricula=enturmado.matricula).count() == 1

    corpo["registros"][0]["presente"] = True
    resposta = autenticado.post("/api/v1/frequencias/lote/", corpo, format="json")
    assert resposta.status_code == 201
    assert Frequencia.objects.filter(matricula=enturmado.matricula).count() == 1
    assert Frequencia.objects.get(matricula=enturmado.matricula).presente is True


def test_resumo_de_frequencia(autenticado, enturmado, turma):
    for dia, presente in enumerate([True, True, False, True]):
        Frequencia.objects.create(
            matricula=enturmado.matricula, turma=turma, data=dt.date(2026, 3, 2 + dia), presente=presente
        )
    resposta = autenticado.get(f"/api/v1/matriculas/{enturmado.matricula_id}/frequencia/")
    assert resposta.status_code == 200
    assert resposta.data["percentual"] == 75.0
    assert resposta.data["faltas"] == 1


def test_gestor_nao_lanca_chamada_de_outra_escola(
    api, gestor_user, outra_escola, serie, matricula, turma
):
    from apps.schools.models import Turma

    turma_externa = Turma.objects.create(escola=outra_escola, serie=serie, nome="Turma X", ano=2026)
    api.force_authenticate(user=gestor_user)
    resposta = api.post(
        "/api/v1/frequencias/lote/",
        {
            "turma": turma_externa.id,
            "data": "2026-03-10",
            "registros": [{"matricula": matricula.id, "presente": True}],
        },
        format="json",
    )
    assert resposta.status_code == 403
