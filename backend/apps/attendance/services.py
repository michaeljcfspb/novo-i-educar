"""Indicadores de frequência."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from .models import Frequencia


def resumo_frequencia(matricula) -> dict:
    registros = Frequencia.objects.filter(matricula=matricula)
    total = registros.count()
    presencas = registros.filter(presente=True).count()
    faltas = total - presencas
    percentual = Decimal("0")
    if total:
        percentual = (Decimal(presencas) / Decimal(total) * 100).quantize(
            Decimal("0.1"), rounding=ROUND_HALF_UP
        )
    return {
        "dias_registrados": total,
        "presencas": presencas,
        "faltas": faltas,
        "percentual": float(percentual),
    }
