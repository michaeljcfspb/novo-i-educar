"""Montagem do pacote de exportação do Censo Escolar.

O formato segue os blocos do Censo (escola, turmas, alunos, matrículas e
profissionais). A validação aponta pendências antes do envio.
"""
from __future__ import annotations

from django.db.models import Max
from django.utils import timezone

from apps.enrollments.models import Matricula
from apps.people.models import Servidor
from apps.schools.models import Turma

from .models import ExportacaoCenso, StatusExportacao


def _pendencia(entidade: str, identificador: str, campo: str, mensagem: str) -> dict:
    return {
        "entidade": entidade,
        "identificador": identificador,
        "campo": campo,
        "mensagem": mensagem,
    }


def montar_payload(escola, ano: int) -> tuple[dict, list[dict]]:
    pendencias: list[dict] = []

    if not escola.codigo_inep:
        pendencias.append(_pendencia("escola", escola.nome, "codigo_inep", "Escola sem código INEP."))

    turmas = list(Turma.objects.filter(escola=escola, ano=ano, ativo=True).select_related("serie"))
    turmas_payload = []
    for turma in turmas:
        if not turma.codigo_inep:
            pendencias.append(
                _pendencia("turma", turma.nome, "codigo_inep", "Turma sem código INEP.")
            )
        matriculas = (
            Matricula.objects.filter(
                escola=escola, ano=ano, serie=turma.serie, ativo=True,
                enturmacoes__turma=turma, enturmacoes__ativo=True,
            )
            .select_related("aluno__pessoa")
            .prefetch_related("aluno__deficiencias")
        )
        alunos_payload = []
        for matricula in matriculas:
            aluno = matricula.aluno
            pessoa = aluno.pessoa
            if not aluno.codigo_inep:
                pendencias.append(
                    _pendencia("aluno", pessoa.nome, "codigo_inep", "Aluno sem código INEP.")
                )
            if not pessoa.data_nascimento:
                pendencias.append(
                    _pendencia("aluno", pessoa.nome, "data_nascimento", "Data de nascimento ausente.")
                )
            if not pessoa.sexo:
                pendencias.append(_pendencia("aluno", pessoa.nome, "sexo", "Sexo não informado."))
            alunos_payload.append(
                {
                    "codigo_aluno": aluno.codigo,
                    "codigo_inep": aluno.codigo_inep,
                    "nome": pessoa.nome,
                    "data_nascimento": pessoa.data_nascimento.isoformat()
                    if pessoa.data_nascimento
                    else None,
                    "sexo": pessoa.sexo,
                    "cpf": pessoa.cpf,
                    "deficiencias": [d.codigo_censo or d.nome for d in aluno.deficiencias.all()],
                    "situacao_matricula": matricula.situacao,
                }
            )
        turmas_payload.append(
            {
                "codigo_turma": turma.nome,
                "codigo_inep": turma.codigo_inep,
                "serie": turma.serie.nome,
                "turno": turma.turno,
                "capacidade": turma.capacidade,
                "alunos": alunos_payload,
            }
        )

    servidores = Servidor.objects.filter(escola=escola, ativo=True).select_related("pessoa")
    profissionais_payload = [
        {
            "nome": servidor.pessoa.nome,
            "cpf": servidor.pessoa.cpf,
            "cargo": servidor.cargo,
            "matricula_funcional": servidor.matricula_funcional,
        }
        for servidor in servidores
    ]

    payload = {
        "gerado_em": timezone.now().isoformat(),
        "ano": ano,
        "escola": {
            "nome": escola.nome,
            "codigo_inep": escola.codigo_inep,
            "sigla": escola.sigla,
            "municipio": escola.municipio.nome if escola.municipio else None,
            "uf": escola.municipio.estado.sigla if escola.municipio else None,
        },
        "turmas": turmas_payload,
        "profissionais": profissionais_payload,
        "totais": {
            "turmas": len(turmas_payload),
            "alunos": sum(len(turma["alunos"]) for turma in turmas_payload),
            "profissionais": len(profissionais_payload),
        },
    }

    return payload, pendencias


def gerar_exportacao(escola, ano: int, usuario=None) -> ExportacaoCenso:
    payload, pendencias = montar_payload(escola, ano)
    versao = (
        ExportacaoCenso.objects.filter(escola=escola, ano=ano).aggregate(maior=Max("versao"))["maior"]
        or 0
    ) + 1
    return ExportacaoCenso.objects.create(
        escola=escola,
        ano=ano,
        versao=versao,
        status=StatusExportacao.VALIDADO if not pendencias else StatusExportacao.GERADO,
        total_alunos=payload["totais"]["alunos"],
        total_turmas=payload["totais"]["turmas"],
        pendencias=pendencias,
        payload=payload,
        criado_por=usuario,
    )
