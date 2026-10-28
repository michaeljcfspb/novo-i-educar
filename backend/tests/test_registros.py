import datetime as dt
from decimal import Decimal

import pytest

from apps.assessment.models import Nota
from apps.attendance.models import Frequencia
from apps.enrollments.models import SituacaoMatricula
from apps.records.models import Documento, HistoricoEscolar, SituacaoHistorico, Transferencia

pytestmark = pytest.mark.django_db


def montar_cenario(serie, regra, matricula, enturmado, turma_disciplina, periodos):
    serie.regra_avaliacao = regra
    serie.save(update_fields=["regra_avaliacao"])
    for periodo, valor in zip(periodos, ["8.00", "7.00"]):
        Nota.objects.create(
            matricula=matricula,
            turma_disciplina=turma_disciplina,
            periodo=periodo,
            valor=Decimal(valor),
        )
    for dia in range(4):
        Frequencia.objects.create(
            matricula=matricula, turma=enturmado.turma, data=dt.date(2026, 3, 2 + dia), presente=True
        )


def test_gera_historico_com_disciplinas(
    autenticado, serie, regra, matricula, enturmado, turma_disciplina, periodos
):
    montar_cenario(serie, regra, matricula, enturmado, turma_disciplina, periodos)
    resposta = autenticado.post("/api/v1/historicos/gerar/", {"matricula": matricula.id}, format="json")
    assert resposta.status_code == 201, resposta.data
    assert resposta.data["media_geral"] == "7.50"
    assert resposta.data["situacao"] == "aprovado"
    assert len(resposta.data["disciplinas"]) == 1
    assert resposta.data["disciplinas"][0]["nome_disciplina"] == turma_disciplina.disciplina.nome
    assert resposta.data["frequencia_percentual"] == "100.00"


def test_gerar_historico_e_idempotente(
    autenticado, serie, regra, matricula, enturmado, turma_disciplina, periodos
):
    montar_cenario(serie, regra, matricula, enturmado, turma_disciplina, periodos)
    autenticado.post("/api/v1/historicos/gerar/", {"matricula": matricula.id}, format="json")
    autenticado.post("/api/v1/historicos/gerar/", {"matricula": matricula.id}, format="json")
    assert HistoricoEscolar.objects.filter(aluno=matricula.aluno).count() == 1
    assert HistoricoEscolar.objects.get().disciplinas.count() == 1


def test_gestor_de_outra_escola_nao_gera_historico(
    api, gestor_user, serie, regra, matricula, outra_escola, instituicao, aluno
):
    from apps.enrollments.models import Matricula

    serie.regra_avaliacao = regra
    serie.save(update_fields=["regra_avaliacao"])
    matricula.ativo = False
    matricula.save(update_fields=["ativo"])
    externa = Matricula.objects.create(
        aluno=aluno, escola=outra_escola, serie=serie, curso=serie.curso, ano=2026,
        data_matricula=dt.date(2026, 2, 1),
    )
    api.force_authenticate(user=gestor_user)
    resposta = api.post("/api/v1/historicos/gerar/", {"matricula": externa.id}, format="json")
    assert resposta.status_code == 403


def test_transferencia_de_saida_encerra_matricula(autenticado, matricula, enturmado, outra_escola):
    resposta = autenticado.post(
        "/api/v1/transferencias/",
        {
            "matricula": matricula.id,
            "tipo": "saida",
            "data": "2026-06-30",
            "escola_destino": outra_escola.id,
            "motivo": "mudanca_endereco",
        },
        format="json",
    )
    assert resposta.status_code == 201, resposta.data
    matricula.refresh_from_db()
    enturmado.refresh_from_db()
    assert matricula.situacao == SituacaoMatricula.TRANSFERIDO
    assert matricula.ativo is False
    assert enturmado.ativo is False


def test_transferencia_sem_destino_e_rejeitada(autenticado, matricula):
    resposta = autenticado.post(
        "/api/v1/transferencias/",
        {"matricula": matricula.id, "tipo": "saida", "data": "2026-06-30"},
        format="json",
    )
    assert resposta.status_code == 400
    assert "escola_destino" in resposta.data


def test_transferencia_duplicada_e_rejeitada(autenticado, matricula, outra_escola):
    corpo = {
        "matricula": matricula.id,
        "tipo": "saida",
        "data": "2026-06-30",
        "escola_destino": outra_escola.id,
    }
    assert autenticado.post("/api/v1/transferencias/", corpo, format="json").status_code == 201
    resposta = autenticado.post("/api/v1/transferencias/", corpo, format="json")
    assert resposta.status_code == 400
    assert Transferencia.objects.filter(matricula=matricula, tipo="saida").count() == 1


def test_emite_declaracao_de_matricula(autenticado, matricula):
    resposta = autenticado.post(
        "/api/v1/documentos/emitir/",
        {"aluno": matricula.aluno_id, "tipo": "declaracao_matricula", "matricula": matricula.id},
        format="json",
    )
    assert resposta.status_code == 201, resposta.data
    assert resposta.data["numero"].startswith("DOC-")
    assert "regularmente matriculado" in resposta.data["corpo"]
    assert Documento.objects.count() == 1


def test_emite_declaracao_de_frequencia(
    autenticado, matricula, enturmado, turma
):
    for dia in range(2):
        Frequencia.objects.create(
            matricula=matricula, turma=turma, data=dt.date(2026, 3, 2 + dia), presente=dia == 0
        )
    resposta = autenticado.post(
        "/api/v1/documentos/emitir/",
        {"aluno": matricula.aluno_id, "tipo": "declaracao_frequencia", "matricula": matricula.id},
        format="json",
    )
    assert resposta.status_code == 201
    assert "50.0%" in resposta.data["corpo"]


def test_lista_documentos_por_escola(api, gestor_user, autenticado, matricula, outra_escola):
    autenticado.post(
        "/api/v1/documentos/emitir/",
        {"aluno": matricula.aluno_id, "tipo": "declaracao_matricula", "matricula": matricula.id},
        format="json",
    )
    api.force_authenticate(user=gestor_user)
    resposta = api.get("/api/v1/documentos/")
    assert resposta.status_code == 200
    assert resposta.data["count"] == 1
