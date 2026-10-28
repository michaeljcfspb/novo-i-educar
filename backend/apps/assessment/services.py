"""Cálculo de médias, frequência e situação final."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP

from .models import Nota, RegraAvaliacao, TipoNota


def arredondar(valor: Decimal, casas: int) -> Decimal:
    expoente = Decimal(1).scaleb(-casas)
    return valor.quantize(expoente, rounding=ROUND_HALF_UP)


@dataclass
class ResultadoDisciplina:
    disciplina: str
    notas: dict[str, Decimal] = field(default_factory=dict)
    recuperacao: Decimal | None = None
    media: Decimal = Decimal("0")
    situacao: str = "cursando"


def regra_da_matricula(matricula) -> RegraAvaliacao | None:
    return getattr(matricula.serie, "regra_avaliacao", None)


def media_periodos(notas: list[Nota], regra: RegraAvaliacao) -> Decimal:
    normais = [n for n in notas if n.tipo == TipoNota.NORMAL]
    if not normais:
        return Decimal("0")
    if regra.tipo_media == "ponderada":
        soma_pesos = sum((n.periodo.peso for n in normais), Decimal("0"))
        if soma_pesos:
            total = sum((n.valor * n.periodo.peso for n in normais), Decimal("0"))
            return arredondar(total / soma_pesos, regra.casas_decimais)
    total = sum((n.valor for n in normais), Decimal("0"))
    return arredondar(total / len(normais), regra.casas_decimais)


def calcular_disciplina(matricula, turma_disciplina, notas: list[Nota]) -> ResultadoDisciplina:
    regra = regra_da_matricula(matricula)
    resultado = ResultadoDisciplina(disciplina=str(turma_disciplina.disciplina))
    if regra is None:
        return resultado

    for nota in notas:
        if nota.tipo == TipoNota.NORMAL:
            resultado.notas[nota.periodo.nome] = nota.valor
        else:
            resultado.recuperacao = nota.valor

    media = media_periodos(notas, regra)
    if (
        regra.permite_recuperacao
        and resultado.recuperacao is not None
        and media < regra.media_aprovacao
        and resultado.recuperacao > media
    ):
        media = arredondar(resultado.recuperacao, regra.casas_decimais)

    resultado.media = media
    return resultado


def situacao_final(media: Decimal, frequencia: Decimal, regra: RegraAvaliacao | None) -> str:
    if regra is None:
        return "sem_regra"
    if frequencia < Decimal(regra.percentual_frequencia):
        return "reprovado_frequencia"
    if media >= regra.media_aprovacao:
        return "aprovado"
    if regra.permite_recuperacao and media >= regra.media_recuperacao:
        return "recuperacao"
    return "reprovado"


def gerar_boletim(matricula) -> dict:
    """Monta o boletim completo: notas por período, médias, frequência e situação."""
    from apps.attendance.services import resumo_frequencia
    from apps.schools.models import TurmaDisciplina

    enturmacao = matricula.enturmacoes.filter(ativo=True).select_related("turma").first()
    turma = enturmacao.turma if enturmacao else None
    regra = regra_da_matricula(matricula)
    frequencia = resumo_frequencia(matricula)

    disciplinas = []
    medias = []
    if turma:
        alocacoes = TurmaDisciplina.objects.filter(turma=turma).select_related(
            "disciplina", "professor__pessoa"
        )
        for alocacao in alocacoes:
            notas = list(matricula.notas.filter(turma_disciplina=alocacao))
            resultado = calcular_disciplina(matricula, alocacao, notas)
            disciplinas.append(
                {
                    "turma_disciplina": alocacao.id,
                    "disciplina": alocacao.disciplina.nome,
                    "professor": (
                        alocacao.professor.pessoa.nome if alocacao.professor else None
                    ),
                    "notas": {chave: float(valor) for chave, valor in resultado.notas.items()},
                    "recuperacao": (
                        float(resultado.recuperacao) if resultado.recuperacao is not None else None
                    ),
                    "media": float(resultado.media),
                }
            )
            if resultado.notas:
                medias.append(resultado.media)

    media_geral = Decimal("0")
    if medias:
        media_geral = arredondar(
            sum(medias, Decimal("0")) / len(medias), regra.casas_decimais if regra else 1
        )

    situacao = situacao_final(media_geral, Decimal(str(frequencia["percentual"])), regra)

    return {
        "matricula": matricula.id,
        "aluno": matricula.aluno.pessoa.nome,
        "ano": matricula.ano,
        "turma": turma.nome if turma else None,
        "regra_avaliacao": regra.nome if regra else None,
        "media_geral": float(media_geral),
        "frequencia": {**frequencia, "minimo": regra.percentual_frequencia if regra else None},
        "situacao_final": situacao,
        "disciplinas": disciplinas,
    }


def validar_nota(matricula, turma_disciplina, periodo, valor) -> str | None:
    """Valida uma nota fora do serializer (usado no lançamento em lote)."""
    if matricula.ano != periodo.ano_letivo.ano:
        return "O período pertence a outro ano letivo."
    enturmacao = matricula.enturmacoes.filter(ativo=True).first()
    if enturmacao is None:
        return "O aluno não está enturmado em nenhuma turma."
    if enturmacao.turma_id != turma_disciplina.turma_id:
        return "A disciplina não pertence à turma atual do aluno."
    regra = regra_da_matricula(matricula)
    if regra and (valor is None or valor < Decimal("0") or valor > regra.nota_maxima):
        return f"A nota deve estar entre 0 e {regra.nota_maxima}."
    return None
