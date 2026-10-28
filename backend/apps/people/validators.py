"""Validadores brasileiros reutilizáveis."""
from __future__ import annotations

import re

from django.core.exceptions import ValidationError


def somente_digitos(valor: str) -> str:
    return re.sub(r"\D", "", valor or "")


def validar_cpf(valor: str) -> None:
    cpf = somente_digitos(valor)
    if len(cpf) != 11:
        raise ValidationError("CPF deve conter 11 dígitos.", code="cpf_invalido")
    if cpf == cpf[0] * 11:
        raise ValidationError("CPF inválido.", code="cpf_invalido")

    def digito(parcial: str) -> str:
        pesos = range(len(parcial) + 1, 1, -1)
        soma = sum(int(d) * p for d, p in zip(parcial, pesos))
        resto = (soma * 10) % 11
        return "0" if resto == 10 else str(resto)

    if cpf[9] != digito(cpf[:9]) or cpf[10] != digito(cpf[:10]):
        raise ValidationError("CPF inválido.", code="cpf_invalido")


def validar_cep(valor: str) -> None:
    if valor and len(somente_digitos(valor)) != 8:
        raise ValidationError("CEP deve conter 8 dígitos.", code="cep_invalido")
