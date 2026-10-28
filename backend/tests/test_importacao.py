import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.integrations.models import EntregaWebhook, Importacao, Webhook
from apps.people.models import Aluno, Pessoa

pytestmark = pytest.mark.django_db


def enviar_csv(api, conteudo: str, nome: str = "alunos.csv"):
    arquivo = SimpleUploadedFile(nome, conteudo.encode("utf-8"), content_type="text/csv")
    return api.post("/api/v1/importacoes/", {"arquivo": arquivo}, format="multipart")


def test_importa_alunos_validos(autenticado):
    csv = (
        "nome,cpf,data_nascimento,sexo,email\n"
        "Joana Prado,52998224725,10/03/2015,F,joana@example.com\n"
        "Lucas Almeida,,12/05/2016,M,lucas@example.com\n"
    )
    resposta = enviar_csv(autenticado, csv)
    assert resposta.status_code == 201, resposta.data
    assert resposta.data["total_sucessos"] == 2
    assert resposta.data["total_erros"] == 0
    assert Aluno.objects.count() == 2
    assert Pessoa.objects.filter(cpf="52998224725").exists()


def test_importacao_relata_erros_por_linha(autenticado, aluno):
    csv = (
        "nome,cpf,data_nascimento,sexo\n"
        "Sem Cpf,,31/02/2015,X\n"
        f"Duplicado,{aluno.pessoa.cpf},10/03/2015,F\n"
        "Valido Souza,11144477735,10/03/2015,M\n"
    )
    resposta = enviar_csv(autenticado, csv)
    assert resposta.status_code == 201
    assert resposta.data["total_sucessos"] == 1
    assert resposta.data["total_erros"] == 2
    linhas = {item["linha"] for item in resposta.data["relatorio"]}
    assert linhas == {2, 3}


def test_arquivo_obrigatorio(autenticado):
    resposta = autenticado.post("/api/v1/importacoes/", {}, format="multipart")
    assert resposta.status_code == 400
    assert "arquivo" in resposta.data


def test_webhook_dispara_evento(autenticado, monkeypatch):
    webhook = Webhook.objects.create(
        nome="ERP", url="https://erp.example.com/hook", eventos=["matricula.criada"]
    )

    class RespostaFalsa:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(
        "apps.integrations.services.urllib.request.urlopen", lambda *a, **k: RespostaFalsa()
    )

    resposta = autenticado.post(f"/api/v1/webhooks/{webhook.pk}/testar/")
    assert resposta.status_code == 200
    assert resposta.data["sucesso"] is True
    assert EntregaWebhook.objects.count() == 1
    assert EntregaWebhook.objects.get().status_code == 200


def test_importacao_aparece_na_listagem(autenticado):
    enviar_csv(autenticado, "nome\nMaria Teste\n")
    resposta = autenticado.get("/api/v1/importacoes/")
    assert resposta.status_code == 200
    assert resposta.data["count"] == 1
    assert Importacao.objects.count() == 1
