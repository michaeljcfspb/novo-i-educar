"""Fixtures compartilhadas dos testes de API."""
from __future__ import annotations

import datetime as dt

import pytest
from rest_framework.test import APIClient

from decimal import Decimal

from apps.accounts.models import PerfilUsuario, User
from apps.assessment.models import Nota, PeriodoAvaliacao, RegraAvaliacao
from apps.attendance.models import Frequencia
from apps.core.models import Estado, Municipio
from apps.enrollments.models import Matricula
from apps.people.models import Aluno, Deficiencia, Pessoa
from apps.people.models import CargoServidor, Servidor
from apps.schools.models import (
    AnoLetivo,
    Calendario,
    CalendarioDia,
    Curso,
    Disciplina,
    Escola,
    Instituicao,
    Serie,
    Turma,
    TurmaDisciplina,
)


@pytest.fixture
def api() -> APIClient:
    return APIClient()


@pytest.fixture
def uf(db) -> Estado:
    return Estado.objects.create(nome="Paraná", sigla="PR", codigo_ibge="41")


@pytest.fixture
def municipio(uf) -> Municipio:
    return Municipio.objects.create(nome="Curitiba", estado=uf, codigo_ibge="4106902")


@pytest.fixture
def instituicao(municipio) -> Instituicao:
    return Instituicao.objects.create(
        nome="Secretaria Municipal de Educação", sigla="SME", municipio=municipio
    )


@pytest.fixture
def escola(instituicao, municipio) -> Escola:
    return Escola.objects.create(
        instituicao=instituicao, nome="Escola Municipal Centro", sigla="EMC", municipio=municipio
    )


@pytest.fixture
def outra_escola(instituicao) -> Escola:
    return Escola.objects.create(
        instituicao=instituicao, nome="Escola Municipal Norte", sigla="EMN"
    )


@pytest.fixture
def curso(instituicao) -> Curso:
    return Curso.objects.create(
        instituicao=instituicao, nome="Ensino Fundamental", sigla="EF", nivel_ensino="fundamental"
    )


@pytest.fixture
def serie(curso) -> Serie:
    return Serie.objects.create(
        curso=curso, nome="1º Ano", etapa=1, carga_horaria=800, idade_inicial=6, idade_final=7
    )


@pytest.fixture
def disciplina(instituicao) -> Disciplina:
    return Disciplina.objects.create(
        instituicao=instituicao, nome="Matemática", sigla="MAT", carga_horaria=200
    )


@pytest.fixture
def turma(escola, serie) -> Turma:
    return Turma.objects.create(
        escola=escola, serie=serie, nome="1º Ano A", ano=2026, turno="matutino", capacidade=2
    )


@pytest.fixture
def deficiencia(db) -> Deficiencia:
    return Deficiencia.objects.create(nome="Baixa visão", codigo_censo="03")


@pytest.fixture
def pessoa(municipio) -> Pessoa:
    return Pessoa.objects.create(
        nome="Maria da Silva",
        cpf="52998224725",
        data_nascimento=dt.date(2015, 3, 10),
        sexo="F",
        municipio=municipio,
    )


@pytest.fixture
def aluno(pessoa) -> Aluno:
    return Aluno.objects.create(pessoa=pessoa)


@pytest.fixture
def matricula(aluno, escola, serie, curso) -> Matricula:
    return Matricula.objects.create(
        aluno=aluno, escola=escola, serie=serie, curso=curso, ano=2026, data_matricula=dt.date(2026, 2, 1)
    )


@pytest.fixture
def admin_user(db) -> User:
    return User.objects.create_superuser(
        email="admin@example.com", password="senha-forte-123", nome_completo="Admin"
    )


@pytest.fixture
def gestor_user(escola) -> User:
    return User.objects.create_user(
        email="gestor@example.com",
        password="senha-forte-123",
        nome_completo="Gestor EMC",
        perfil=PerfilUsuario.GESTOR,
        escola=escola,
    )


@pytest.fixture
def consulta_user(escola) -> User:
    return User.objects.create_user(
        email="consulta@example.com",
        password="senha-forte-123",
        nome_completo="Consulta",
        perfil=PerfilUsuario.CONSULTA,
        escola=escola,
    )


@pytest.fixture
def autenticado(api, admin_user) -> APIClient:
    api.force_authenticate(user=admin_user)
    return api


@pytest.fixture
def regra(db) -> RegraAvaliacao:
    return RegraAvaliacao.objects.create(
        nome="Regra padrão",
        nota_maxima=Decimal("10.00"),
        media_aprovacao=Decimal("6.00"),
        media_recuperacao=Decimal("5.00"),
        percentual_frequencia=75,
        casas_decimais=1,
    )


@pytest.fixture
def ano_letivo(instituicao) -> AnoLetivo:
    return AnoLetivo.objects.create(
        instituicao=instituicao,
        ano=2026,
        data_inicio=dt.date(2026, 2, 2),
        data_fim=dt.date(2026, 12, 18),
    )


@pytest.fixture
def periodos(ano_letivo) -> list[PeriodoAvaliacao]:
    return [
        PeriodoAvaliacao.objects.create(
            ano_letivo=ano_letivo,
            nome=f"{ordem}º Bimestre",
            ordem=ordem,
            data_inicio=dt.date(2026, ordem * 2, 1),
            data_fim=dt.date(2026, ordem * 2 + 1, 28),
        )
        for ordem in (1, 2)
    ]


@pytest.fixture
def servidor_professor(escola, disciplina) -> Servidor:
    pessoa = Pessoa.objects.create(nome="Professor Teste", cpf="01370154962")
    servidor = Servidor.objects.create(
        pessoa=pessoa, escola=escola, cargo=CargoServidor.PROFESSOR
    )
    servidor.disciplinas.add(disciplina)
    return servidor


@pytest.fixture
def professor_user(escola, servidor_professor) -> User:
    return User.objects.create_user(
        email="professor@example.com",
        password="senha-forte-123",
        nome_completo="Professor Teste",
        perfil=PerfilUsuario.PROFESSOR,
        escola=escola,
        servidor=servidor_professor,
    )


@pytest.fixture
def turma_disciplina(turma, disciplina, servidor_professor) -> TurmaDisciplina:
    return TurmaDisciplina.objects.create(
        turma=turma, disciplina=disciplina, professor=servidor_professor, carga_horaria=200
    )


@pytest.fixture
def enturmado(matricula, turma) -> "MatriculaTurma":
    from apps.enrollments.models import MatriculaTurma

    return MatriculaTurma.objects.create(
        matricula=matricula, turma=turma, data_enturmacao=dt.date(2026, 2, 5)
    )


@pytest.fixture
def calendario(ano_letivo, escola) -> Calendario:
    return Calendario.objects.create(ano_letivo=ano_letivo, escola=escola, nome="Calendário")
