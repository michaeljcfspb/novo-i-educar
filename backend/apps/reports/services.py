"""Indicadores e relatórios agregados da rede."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Avg, Count, Q

from apps.attendance.models import Frequencia
from apps.enrollments.models import Matricula, SituacaoMatricula
from apps.schools.models import Escola, Turma


def _percentual(parte: int, total: int) -> float:
    if not total:
        return 0.0
    return float((Decimal(parte) / Decimal(total) * 100).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def _queryset_matriculas(ano: int, escola=None):
    qs = Matricula.objects.filter(ano=ano)
    if escola is not None:
        qs = qs.filter(escola=escola)
    return qs


def indicadores_rede(ano: int, escola=None) -> dict:
    matriculas = _queryset_matriculas(ano, escola)
    total = matriculas.count()
    por_situacao = {
        item["situacao"]: item["total"]
        for item in matriculas.values("situacao").annotate(total=Count("id"))
    }
    ativas = matriculas.filter(ativo=True).count()

    turmas = Turma.objects.filter(ano=ano, ativo=True)
    if escola is not None:
        turmas = turmas.filter(escola=escola)

    ocupacao = []
    for turma in turmas:
        ocupadas = turma.matriculas.filter(ativo=True).count()
        if turma.capacidade:
            ocupacao.append(min(ocupadas / turma.capacidade, 1.0))
    ocupacao_media = _percentual(int(sum(ocupacao) * 100), max(len(ocupacao), 1)) if ocupacao else 0.0

    frequencias = Frequencia.objects.filter(matricula__in=matriculas)
    total_freq = frequencias.count()
    presencas = frequencias.filter(presente=True).count()

    media_notas = (
        matriculas.filter(notas__isnull=False).aggregate(media=Avg("notas__valor"))["media"]
        or Decimal("0")
    )

    aprovados = por_situacao.get(SituacaoMatricula.APROVADO, 0)
    reprovados = por_situacao.get(SituacaoMatricula.REPROVADO, 0)
    abandonos = por_situacao.get(SituacaoMatricula.ABANDONOU, 0)
    transferidos = por_situacao.get(SituacaoMatricula.TRANSFERIDO, 0)

    return {
        "ano": ano,
        "total_matriculas": total,
        "matriculas_ativas": ativas,
        "escolas": Escola.objects.filter(matriculas__ano=ano).distinct().count()
        if escola is None
        else 1,
        "turmas": turmas.count(),
        "taxa_aprovacao": _percentual(aprovados, total),
        "taxa_reprovacao": _percentual(reprovados, total),
        "taxa_abandono": _percentual(abandonos, total),
        "taxa_transferencia": _percentual(transferidos, total),
        "ocupacao_media": ocupacao_media,
        "frequencia_media": _percentual(presencas, total_freq),
        "media_geral": float(Decimal(media_notas).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)),
        "situacoes": por_situacao,
    }


def relatorio_turmas(ano: int, escola=None) -> list[dict]:
    turmas = Turma.objects.filter(ano=ano).select_related("escola", "serie")
    if escola is not None:
        turmas = turmas.filter(escola=escola)

    linhas = []
    for turma in turmas:
        matriculas = turma.matriculas.filter(ativo=True)
        total = matriculas.count()
        notas = Matricula.objects.filter(id__in=matriculas.values("id")).aggregate(
            media=Avg("notas__valor")
        )["media"] or Decimal("0")
        frequencias = Frequencia.objects.filter(turma=turma)
        total_freq = frequencias.count()
        presencas = frequencias.filter(presente=True).count()
        linhas.append(
            {
                "turma": turma.nome,
                "escola": turma.escola.nome,
                "serie": turma.serie.nome,
                "turno": turma.turno,
                "capacidade": turma.capacidade,
                "alunos": total,
                "ocupacao": _percentual(total, turma.capacidade or 0),
                "media": float(Decimal(notas).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)),
                "frequencia": _percentual(presencas, total_freq),
            }
        )
    return linhas


def alunos_em_risco(ano: int, escola=None, frequencia_minima: int = 75, media_minima: float = 6.0) -> list[dict]:
    """Alunos com frequência ou média abaixo do mínimo configurado."""
    from apps.assessment.services import gerar_boletim

    matriculas = (
        _queryset_matriculas(ano, escola)
        .filter(ativo=True)
        .select_related("aluno__pessoa", "escola", "serie")
    )
    risco = []
    for matricula in matriculas:
        boletim = gerar_boletim(matricula)
        frequencia = boletim["frequencia"]["percentual"]
        media = boletim["media_geral"]
        if frequencia < frequencia_minima or media < media_minima:
            risco.append(
                {
                    "matricula": matricula.id,
                    "aluno": matricula.aluno.pessoa.nome,
                    "escola": matricula.escola.nome,
                    "serie": matricula.serie.nome,
                    "frequencia": frequencia,
                    "media": media,
                    "motivo": (
                        "Frequência baixa"
                        if frequencia < frequencia_minima
                        else "Média abaixo do mínimo"
                    ),
                }
            )
    return risco
