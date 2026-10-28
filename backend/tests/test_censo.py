import pytest

from apps.censo.models import ExportacaoCenso

pytestmark = pytest.mark.django_db


def test_preview_aponta_pendencias(autenticado, escola, turma, matricula, enturmado):
    resposta = autenticado.post(
        "/api/v1/censo/exportacoes/preview/",
        {"escola": escola.id, "ano": 2026},
        format="json",
    )
    assert resposta.status_code == 200, resposta.data
    campos = {item["campo"] for item in resposta.data["pendencias"]}
    assert {"codigo_inep"} <= campos
    assert resposta.data["totais"]["alunos"] == 1


def test_gera_exportacao_com_pendencias(autenticado, escola, turma, matricula, enturmado, aluno):
    resposta = autenticado.post(
        "/api/v1/censo/exportacoes/gerar/",
        {"escola": escola.id, "ano": 2026},
        format="json",
    )
    assert resposta.status_code == 201, resposta.data
    assert resposta.data["status"] == "gerado"
    assert resposta.data["total_alunos"] == 1
    assert resposta.data["payload"]["escola"]["nome"] == escola.nome


def test_exportacao_valida_quando_codigos_existem(
    autenticado, escola, turma, matricula, enturmado, aluno
):
    escola.codigo_inep = "41000001"
    escola.save(update_fields=["codigo_inep"])
    turma.codigo_inep = "4100000101"
    turma.save(update_fields=["codigo_inep"])
    aluno.codigo_inep = "410000010001"
    aluno.save(update_fields=["codigo_inep"])
    aluno.pessoa.sexo = "F"
    aluno.pessoa.save(update_fields=["sexo"])

    resposta = autenticado.post(
        "/api/v1/censo/exportacoes/gerar/",
        {"escola": escola.id, "ano": 2026},
        format="json",
    )
    assert resposta.status_code == 201, resposta.data
    assert resposta.data["status"] == "validado"
    assert resposta.data["pendencias"] == []
    turma_payload = resposta.data["payload"]["turmas"][0]
    assert turma_payload["codigo_inep"] == "4100000101"
    assert turma_payload["alunos"][0]["codigo_inep"] == "410000010001"


def test_versoes_incrementais(autenticado, escola, turma, matricula, enturmado, aluno):
    primeira = autenticado.post(
        "/api/v1/censo/exportacoes/gerar/", {"escola": escola.id, "ano": 2026}, format="json"
    )
    segunda = autenticado.post(
        "/api/v1/censo/exportacoes/gerar/", {"escola": escola.id, "ano": 2026}, format="json"
    )
    assert primeira.data["versao"] == 1
    assert segunda.data["versao"] == 2
    assert ExportacaoCenso.objects.count() == 2


def test_gestor_de_outra_escola_nao_exporta(api, gestor_user, outra_escola):
    api.force_authenticate(user=gestor_user)
    resposta = api.post(
        "/api/v1/censo/exportacoes/gerar/",
        {"escola": outra_escola.id, "ano": 2026},
        format="json",
    )
    assert resposta.status_code == 403
