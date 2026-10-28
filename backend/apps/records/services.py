"""Geração de histórico escolar, transferências e documentos."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.assessment.services import calcular_disciplina, gerar_boletim
from apps.attendance.services import resumo_frequencia
from apps.enrollments.models import SituacaoMatricula

from .models import (
    Documento,
    HistoricoDisciplina,
    HistoricoEscolar,
    SituacaoHistorico,
    TipoDocumento,
    TipoTransferencia,
    Transferencia,
)

MAPA_SITUACAO = {
    "aprovado": SituacaoHistorico.APROVADO,
    "recuperacao": SituacaoHistorico.EM_CURSO,
    "reprovado": SituacaoHistorico.REPROVADO,
    "reprovado_frequencia": SituacaoHistorico.REPROVADO,
    "transferido": SituacaoHistorico.TRANSFERIDO,
}


@transaction.atomic
def gerar_historico(matricula, usuario=None) -> HistoricoEscolar:
    """Consolida notas e frequência da matrícula em um histórico escolar."""
    enturmacao = matricula.enturmacoes.filter(ativo=True).select_related("turma").first()
    turma = enturmacao.turma if enturmacao else None
    frequencia = resumo_frequencia(matricula)
    boletim = gerar_boletim(matricula)

    historico, _ = HistoricoEscolar.objects.update_or_create(
        aluno=matricula.aluno,
        ano=matricula.ano,
        serie=matricula.serie,
        defaults={
            "matricula": matricula,
            "escola": matricula.escola,
            "carga_horaria_total": matricula.serie.carga_horaria,
            "dias_letivos": frequencia["dias_registrados"],
            "frequencia_percentual": Decimal(str(frequencia["percentual"])),
            "media_geral": Decimal(str(boletim["media_geral"])),
            "situacao": MAPA_SITUACAO.get(boletim["situacao_final"], SituacaoHistorico.EM_CURSO),
            "criado_por": usuario,
        },
    )

    if turma:
        historico.disciplinas.all().delete()
        for alocacao in turma.disciplinas.select_related("disciplina").all():
            notas = list(matricula.notas.filter(turma_disciplina=alocacao))
            resultado = calcular_disciplina(matricula, alocacao, notas)
            HistoricoDisciplina.objects.create(
                historico=historico,
                disciplina=alocacao.disciplina,
                nome_disciplina=alocacao.disciplina.nome,
                carga_horaria=alocacao.carga_horaria or alocacao.disciplina.carga_horaria,
                media=resultado.media,
                frequencia=Decimal(str(frequencia["percentual"])),
                situacao=(
                    SituacaoHistorico.APROVADO
                    if resultado.media >= (matricula.serie.regra_avaliacao.media_aprovacao
                                           if matricula.serie.regra_avaliacao else Decimal("6"))
                    else SituacaoHistorico.REPROVADO
                ),
            )
    return historico


@transaction.atomic
def registrar_transferencia(
    matricula,
    tipo: str,
    data_movimento: date,
    escola_destino=None,
    motivo: str = "pedido_responsavel",
    observacao: str = "",
    usuario=None,
) -> Transferencia:
    transferencia = Transferencia.objects.create(
        matricula=matricula,
        tipo=tipo,
        data=data_movimento,
        escola_origem=matricula.escola,
        escola_destino=escola_destino,
        motivo=motivo,
        observacao=observacao,
        criado_por=usuario,
    )
    if tipo == TipoTransferencia.SAIDA:
        matricula.situacao = SituacaoMatricula.TRANSFERIDO
        matricula.ativo = False
        matricula.save(update_fields=["situacao", "ativo", "atualizado_em"])
        matricula.enturmacoes.filter(ativo=True).update(ativo=False)
        HistoricoEscolar.objects.filter(matricula=matricula).update(
            situacao=SituacaoHistorico.TRANSFERIDO
        )
    return transferencia


def montar_corpo_documento(tipo: str, aluno, matricula=None) -> tuple[str, str]:
    """Monta título e corpo padrão de cada tipo de documento."""
    nome = aluno.pessoa.nome
    escola = matricula.escola.nome if matricula else "—"
    serie = matricula.serie.nome if matricula else "—"
    ano = matricula.ano if matricula else timezone.localdate().year
    hoje = timezone.localdate().strftime("%d/%m/%Y")

    if tipo == TipoDocumento.DECLARACAO_MATRICULA:
        titulo = "Declaração de matrícula"
        corpo = (
            f"Declaramos, para os devidos fins, que {nome} está regularmente matriculado(a) "
            f"na {escola}, na série {serie}, no ano letivo de {ano}.\n\n"
            f"Emitido em {hoje}."
        )
    elif tipo == TipoDocumento.DECLARACAO_FREQUENCIA:
        resumo = resumo_frequencia(matricula) if matricula else {"percentual": 0}
        titulo = "Declaração de frequência"
        corpo = (
            f"Declaramos que {nome}, matrícula {getattr(matricula, 'id', '—')}, "
            f"apresenta frequência de {resumo['percentual']}% no ano letivo de {ano}.\n\n"
            f"Emitido em {hoje}."
        )
    elif tipo == TipoDocumento.DECLARACAO_CONCLUSAO:
        titulo = "Declaração de conclusão"
        corpo = (
            f"Declaramos que {nome} concluiu a série {serie} na {escola} no ano letivo de {ano}.\n\n"
            f"Emitido em {hoje}."
        )
    elif tipo == TipoDocumento.HISTORICO_ESCOLAR:
        titulo = "Histórico escolar"
        corpo = (
            f"Histórico escolar de {nome}, referente à série {serie} na {escola}, "
            f"ano letivo de {ano}.\n\nEmitido em {hoje}."
        )
    else:
        titulo = "Guia de transferência"
        corpo = (
            f"Transferência de {nome}, da {escola} (série {serie}, {ano}).\n\nEmitido em {hoje}."
        )
    return titulo, corpo


def emitir_documento(aluno, tipo: str, matricula=None, usuario=None) -> Documento:
    titulo, corpo = montar_corpo_documento(tipo, aluno, matricula)
    return Documento.objects.create(
        aluno=aluno,
        matricula=matricula,
        tipo=tipo,
        titulo=titulo,
        corpo=corpo,
        criado_por=usuario,
    )
