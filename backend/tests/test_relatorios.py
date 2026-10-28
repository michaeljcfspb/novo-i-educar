import datetime as dt
from decimal import Decimal

import pytest

from apps.assessment.models import Nota
from apps.attendance.models import Frequencia

pytestmark = pytest.mark.django_db


def preparar_dados(serie, regra, matricula, enturmado, turma_disciplina, periodos):
    serie.regra_avaliacao = regra
    serie.save(update_fields=["regra_avaliacao"])
    Nota.objects.create(
        matricula=matricula, turma_disciplina=turma_disciplina, periodo=periodos[0],
        valor=Decimal("8.00"),
    )
    for dia in range(4):
        Frequencia.objects.create(
            matricula=matricula, turma=enturmado.turma, data=dt.date(2026, 3, 2 + dia), presente=True
        )


def test_indicadores_da_rede(autenticado, serie, regra, matricula, enturmado, turma_disciplina, periodos, escola):
    preparar_dados(serie, regra, matricula, enturmado, turma_disciplina, periodos)
    resposta = autenticado.get("/api/v1/relatorios/indicadores/?ano=2026")
    assert resposta.status_code == 200, resposta.data
    assert resposta.data["total_matriculas"] == 1
    assert resposta.data["turmas"] == 1
    assert resposta.data["frequencia_media"] == 100.0
    assert resposta.data["media_geral"] == 8.0
    assert resposta.data["escolas"] == 1


def test_relatorio_de_turmas(autenticado, serie, regra, matricula, enturmado, turma_disciplina, periodos):
    preparar_dados(serie, regra, matricula, enturmado, turma_disciplina, periodos)
    resposta = autenticado.get("/api/v1/relatorios/turmas/?ano=2026")
    assert resposta.status_code == 200
    assert len(resposta.data) == 1
    linha = resposta.data[0]
    assert linha["alunos"] == 1
    assert linha["capacidade"] == 2
    assert linha["ocupacao"] == 50.0
    assert linha["media"] == 8.0


def test_exportacao_csv(autenticado, turma):
    resposta = autenticado.get("/api/v1/relatorios/turmas.csv?ano=2026")
    assert resposta.status_code == 200
    assert resposta["Content-Type"].startswith("text/csv")
    assert "attachment" in resposta["Content-Disposition"]
    corpo = resposta.content.decode("utf-8-sig")
    assert "Turma;Escola;Série" in corpo
    assert turma.nome in corpo


def test_alunos_em_risco(autenticado, serie, regra, matricula, enturmado, turma_disciplina, turma):
    serie.regra_avaliacao = regra
    serie.save(update_fields=["regra_avaliacao"])
    for dia in range(4):
        Frequencia.objects.create(
            matricula=matricula, turma=turma, data=dt.date(2026, 3, 2 + dia), presente=dia == 0
        )
    resposta = autenticado.get("/api/v1/relatorios/alunos-risco/?ano=2026")
    assert resposta.status_code == 200
    assert len(resposta.data) == 1
    assert "Frequência baixa" in resposta.data[0]["motivo"]


def test_boletim_em_pdf(autenticado, serie, regra, matricula, enturmado, turma_disciplina, periodos):
    preparar_dados(serie, regra, matricula, enturmado, turma_disciplina, periodos)
    resposta = autenticado.get(f"/api/v1/matriculas/{matricula.pk}/boletim-pdf/")
    assert resposta.status_code == 200
    assert resposta["Content-Type"] == "application/pdf"
    assert resposta.content.startswith(b"%PDF")


def test_historico_em_pdf(autenticado, serie, regra, matricula, enturmado, turma_disciplina, periodos):
    preparar_dados(serie, regra, matricula, enturmado, turma_disciplina, periodos)
    gerado = autenticado.post("/api/v1/historicos/gerar/", {"matricula": matricula.id}, format="json")
    historico_id = gerado.data["id"]
    resposta = autenticado.get(f"/api/v1/historicos/{historico_id}/pdf/")
    assert resposta.status_code == 200
    assert resposta.content.startswith(b"%PDF")


def test_portal_sem_aluno_vinculado(autenticado):
    resposta = autenticado.get("/api/v1/portal/boletim/")
    assert resposta.status_code == 404
    assert "não está vinculado" in resposta.data["detail"]


def test_portal_do_aluno(api, aluno, matricula, enturmado, escola):
    from apps.accounts.models import User

    usuario = User.objects.create_user(
        email="aluno@example.com",
        password="senha-forte-123",
        nome_completo=aluno.pessoa.nome,
        perfil="consulta",
        escola=escola,
        aluno=aluno,
    )
    api.force_authenticate(user=usuario)
    perfil = api.get("/api/v1/portal/perfil/")
    assert perfil.status_code == 200
    assert perfil.data["codigo"] == aluno.codigo
    assert perfil.data["matriculas"][0]["ano"] == 2026

    boletim = api.get("/api/v1/portal/boletim/")
    assert boletim.status_code == 200
    assert boletim.data["matricula"] == matricula.id

    frequencia = api.get("/api/v1/portal/frequencia/")
    assert frequencia.status_code == 200
    assert "percentual" in frequencia.data
