"""Importação de alunos via CSV e disparo de webhooks."""
from __future__ import annotations

import csv
import io
import json
import logging
import urllib.error
import urllib.request
from datetime import datetime

from django.db import transaction

from apps.people.models import Aluno, Pessoa
from apps.people.validators import validar_cpf

from .models import EntregaWebhook, Importacao, StatusImportacao, Webhook

logger = logging.getLogger(__name__)

COLUNAS_OBRIGATORIAS = {"nome"}


def _ler_csv(conteudo: bytes) -> list[dict]:
    texto = conteudo.decode("utf-8-sig", errors="replace")
    primeira = texto.splitlines()[0] if texto else ""
    delimitador = ";" if primeira.count(";") > primeira.count(",") else ","
    leitor = csv.DictReader(io.StringIO(texto), delimiter=delimitador)
    return [{(chave or "").strip().lower(): (valor or "").strip() for chave, valor in linha.items()} for linha in leitor]


def _parse_data(valor: str):
    for formato in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(valor, formato).date()
        except ValueError:
            continue
    return None


@transaction.atomic
def importar_alunos(conteudo: bytes, nome_arquivo: str, usuario=None) -> Importacao:
    importacao = Importacao.objects.create(
        tipo="alunos", arquivo_nome=nome_arquivo, criado_por=usuario
    )
    try:
        linhas = _ler_csv(conteudo)
    except Exception as erro:  # pragma: no cover - arquivo corrompido
        importacao.status = StatusImportacao.FALHOU
        importacao.relatorio = [{"linha": 0, "erro": f"Arquivo inválido: {erro}"}]
        importacao.save(update_fields=["status", "relatorio"])
        return importacao

    relatorio: list[dict] = []
    sucessos = 0
    cpfs_vistos: set[str] = set()

    for indice, linha in enumerate(linhas, start=2):
        erros: list[str] = []
        if not linha.get("nome"):
            erros.append("Coluna 'nome' é obrigatória.")
        if not COLUNAS_OBRIGATORIAS.issubset({chave for chave in linha if linha.get(chave)}):
            erros.append("Cabeçalho inválido: informe ao menos a coluna 'nome'.")

        cpf = (linha.get("cpf") or "").replace(".", "").replace("-", "").strip()
        if cpf:
            try:
                validar_cpf(cpf)
            except Exception:
                erros.append("CPF inválido.")
            if cpf in cpfs_vistos:
                erros.append("CPF repetido no arquivo.")
            if Pessoa.objects.filter(cpf=cpf).exists():
                erros.append("CPF já cadastrado.")
            cpfs_vistos.add(cpf)

        nascimento = None
        if linha.get("data_nascimento"):
            nascimento = _parse_data(linha["data_nascimento"])
            if nascimento is None:
                erros.append("Data de nascimento inválida (use dd/mm/aaaa).")

        sexo = (linha.get("sexo") or "").strip().upper()[:1]
        if sexo and sexo not in {"M", "F"}:
            erros.append("Sexo deve ser M ou F.")

        if erros:
            relatorio.append({"linha": indice, "nome": linha.get("nome"), "erros": erros})
            continue

        pessoa = Pessoa.objects.create(
            nome=linha["nome"],
            cpf=cpf or None,
            data_nascimento=nascimento,
            sexo=sexo if sexo in {"M", "F"} else "",
            email=(linha.get("email") or "").lower(),
            telefone=linha.get("telefone") or "",
            criado_por=usuario,
        )
        Aluno.objects.create(pessoa=pessoa, criado_por=usuario)
        sucessos += 1

    importacao.total_linhas = len(linhas)
    importacao.total_sucessos = sucessos
    importacao.total_erros = len(relatorio)
    importacao.relatorio = relatorio
    importacao.status = (
        StatusImportacao.CONCLUIDA if not relatorio else StatusImportacao.COM_ERROS
    )
    importacao.save()
    return importacao


def disparar_webhook(webhook: Webhook, evento: str, payload: dict) -> EntregaWebhook:
    """Envia o evento de forma síncrona, com timeout curto, e registra o resultado."""
    corpo = json.dumps({"evento": evento, "dados": payload}).encode("utf-8")
    requisicao = urllib.request.Request(
        webhook.url, data=corpo, headers={"Content-Type": "application/json"}, method="POST"
    )
    entrega = EntregaWebhook(webhook=webhook, evento=evento, payload=payload)
    try:
        with urllib.request.urlopen(requisicao, timeout=5) as resposta:
            entrega.status_code = resposta.status
            entrega.sucesso = 200 <= resposta.status < 300
    except urllib.error.HTTPError as erro:
        entrega.status_code = erro.code
        entrega.erro = f"HTTP {erro.code}"
    except Exception as erro:  # pragma: no cover - depende de rede externa
        entrega.erro = str(erro)[:300]
        logger.warning("Falha ao entregar webhook %s: %s", webhook.nome, erro)
    entrega.save()
    return entrega
