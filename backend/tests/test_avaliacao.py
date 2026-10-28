import datetime as dt
from decimal import Decimal

import pytest

from apps.assessment.models import Nota, TipoNota
from apps.attendance.models import Frequencia

pytestmark = pytest.mark.django_db


def preparar(serie, regra):
    serie.regra_avaliacao = regra
    serie.save(update_fields=["regra_avaliacao"])


def test_regra_com_recuperacao_invalida(autenticado):
    resposta = autenticado.post(
        "/api/v1/regras-avaliacao/",
        {
            "nome": "Inválida",
            "nota_maxima": "10.00",
            "media_aprovacao": "6.00",
            "media_recuperacao": "7.00",
        },
        format="json",
    )
    assert resposta.status_code == 400
    assert "media_recuperacao" in resposta.data


def test_nota_acima_do_maximo(autenticado, serie, regra, matricula, enturmado, turma_disciplina, periodos):
    preparar(serie, regra)
    resposta = autenticado.post(
        "/api/v1/notas/",
        {
            "matricula": matricula.id,
            "turma_disciplina": turma_disciplina.id,
            "periodo": periodos[0].id,
            "valor": "11.00",
        },
        format="json",
    )
    assert resposta.status_code == 400
    assert "valor" in resposta.data


def test_professor_nao_lanca_nota_de_outra_turma(
    api, professor_user, serie, regra, matricula, enturmado, turma_disciplina, periodos
):
    from apps.people.models import CargoServidor, Pessoa, Servidor
    from apps.schools.models import Disciplina, TurmaDisciplina

    preparar(serie, regra)
    outro = Servidor.objects.create(
        pessoa=Pessoa.objects.create(nome="Outro Professor"),
        escola=turma_disciplina.turma.escola,
        cargo=CargoServidor.PROFESSOR,
    )
    disciplina = Disciplina.objects.create(
        instituicao=turma_disciplina.turma.escola.instituicao, nome="Ciências", sigla="CIE"
    )
    alocacao = TurmaDisciplina.objects.create(
        turma=turma_disciplina.turma, disciplina=disciplina, professor=outro
    )
    api.force_authenticate(user=professor_user)

    resposta = api.post(
        "/api/v1/notas/",
        {
            "matricula": matricula.id,
            "turma_disciplina": alocacao.id,
            "periodo": periodos[0].id,
            "valor": "8.00",
        },
        format="json",
    )
    assert resposta.status_code == 400
    assert "turma_disciplina" in resposta.data


def test_lancamento_em_lote_cria_e_atualiza(
    autenticado, serie, regra, matricula, enturmado, turma_disciplina, periodos
):
    preparar(serie, regra)
    corpo = {
        "turma_disciplina": turma_disciplina.id,
        "periodo": periodos[0].id,
        "registros": [{"matricula": matricula.id, "valor": "8.50"}],
    }
    resposta = autenticado.post("/api/v1/notas/lote/", corpo, format="json")
    assert resposta.status_code == 201, resposta.data

    corpo["registros"][0]["valor"] = "9.00"
    resposta = autenticado.post("/api/v1/notas/lote/", corpo, format="json")
    assert resposta.status_code == 201
    assert Nota.objects.filter(matricula=matricula).count() == 1
    assert Nota.objects.get(matricula=matricula).valor == Decimal("9.00")


def test_boletim_calcula_media_e_situacao(
    autenticado, serie, regra, matricula, enturmado, turma_disciplina, periodos
):
    preparar(serie, regra)
    for periodo, valor in zip(periodos, ["8.00", "6.00"]):
        Nota.objects.create(
            matricula=matricula, turma_disciplina=turma_disciplina, periodo=periodo, valor=Decimal(valor)
        )
    for dia in range(4):
        Frequencia.objects.create(
            matricula=matricula, turma=enturmado.turma, data=dt.date(2026, 3, 2 + dia), presente=True
        )

    resposta = autenticado.get(f"/api/v1/matriculas/{matricula.pk}/boletim/")
    assert resposta.status_code == 200
    disciplina = resposta.data["disciplinas"][0]
    assert disciplina["media"] == 7.0
    assert resposta.data["frequencia"]["percentual"] == 100.0
    assert resposta.data["situacao_final"] == "aprovado"


def test_recuperacao_substitui_media_baixa(
    autenticado, serie, regra, matricula, enturmado, turma_disciplina, periodos
):
    preparar(serie, regra)
    Nota.objects.create(
        matricula=matricula, turma_disciplina=turma_disciplina, periodo=periodos[0],
        valor=Decimal("4.00"), tipo=TipoNota.NORMAL,
    )
    Nota.objects.create(
        matricula=matricula, turma_disciplina=turma_disciplina, periodo=periodos[0],
        valor=Decimal("6.50"), tipo=TipoNota.RECUPERACAO,
    )
    Frequencia.objects.create(
        matricula=matricula, turma=enturmado.turma, data=dt.date(2026, 3, 2), presente=True
    )

    resposta = autenticado.get(f"/api/v1/matriculas/{matricula.pk}/boletim/")
    disciplina = resposta.data["disciplinas"][0]
    assert disciplina["media"] == 6.5
    assert resposta.data["situacao_final"] == "aprovado"


def test_frequencia_baixa_reprova(
    autenticado, serie, regra, matricula, enturmado, turma_disciplina, periodos
):
    preparar(serie, regra)
    Nota.objects.create(
        matricula=matricula, turma_disciplina=turma_disciplina, periodo=periodos[0], valor=Decimal("9.00")
    )
    for dia in range(4):
        Frequencia.objects.create(
            matricula=matricula, turma=enturmado.turma, data=dt.date(2026, 3, 2 + dia),
            presente=dia == 0,
        )

    resposta = autenticado.get(f"/api/v1/matriculas/{matricula.pk}/boletim/")
    assert resposta.data["frequencia"]["percentual"] == 25.0
    assert resposta.data["situacao_final"] == "reprovado_frequencia"
