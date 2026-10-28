"""Trilha de auditoria automática.

Qualquer modelo que herde `RegistroAuditavel` ganha registros de criação,
atualização e exclusão. A gravação nunca derruba a operação de negócio: falhas
de auditoria são registradas no log e ignoradas.
"""
from __future__ import annotations

import logging
from decimal import Decimal

from django.db.models.signals import post_delete, post_save

from .models import RegistroAuditoria

logger = logging.getLogger(__name__)

CAMPOS_IGNORADOS = {"id", "criado_em", "atualizado_em"}


def serializar(instance) -> dict:
    dados: dict = {}
    for campo in instance._meta.concrete_fields:
        nome = campo.name
        if nome in CAMPOS_IGNORADOS or campo.is_relation and campo.many_to_many:
            continue
        valor = getattr(instance, nome, None)
        if isinstance(valor, Decimal):
            valor = str(valor)
        elif hasattr(valor, "isoformat"):
            valor = valor.isoformat()
        elif not isinstance(valor, (str, int, float, bool, type(None))):
            valor = str(valor)
        dados[nome] = valor
    return dados


def _registrar(instance, acao: str) -> None:
    try:
        RegistroAuditoria.objects.create(
            entidade=f"{instance._meta.app_label}.{instance._meta.model_name}",
            objeto_id=str(instance.pk),
            acao=acao,
            dados=serializar(instance),
            usuario_id=getattr(instance, "criado_por_id", None),
        )
    except Exception:  # pragma: no cover - auditoria nunca interrompe o fluxo
        logger.exception("Falha ao gravar auditoria de %s", instance)


def ao_salvar(sender, instance, created, **kwargs):
    if getattr(sender, "auditar", False):
        _registrar(instance, RegistroAuditoria.Acao.CRIADO if created else RegistroAuditoria.Acao.ATUALIZADO)


def ao_excluir(sender, instance, **kwargs):
    if getattr(sender, "auditar", False):
        _registrar(instance, RegistroAuditoria.Acao.EXCLUIDO)


def conectar() -> None:
    from django.apps import apps

    for modelo in apps.get_models():
        if getattr(modelo, "auditar", False):
            post_save.connect(ao_salvar, sender=modelo, weak=False, dispatch_uid=f"audit_save_{modelo._meta.label_lower}")
            post_delete.connect(ao_excluir, sender=modelo, weak=False, dispatch_uid=f"audit_del_{modelo._meta.label_lower}")
