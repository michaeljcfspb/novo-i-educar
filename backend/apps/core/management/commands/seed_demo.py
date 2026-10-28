"""Popula o banco com uma rede escolar de demonstração.

Uso: python manage.py seed_demo
Idempotente: pode ser executado novamente sem duplicar registros.
"""
from __future__ import annotations

import datetime as dt
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import PerfilUsuario, User
from apps.assessment.models import Nota, PeriodoAvaliacao, RegraAvaliacao, TipoNota
from apps.attendance.models import Frequencia
from apps.core.models import Estado, Municipio
from apps.enrollments.models import Matricula, MatriculaTurma
from apps.people.models import Aluno, CargoServidor, Deficiencia, Pessoa, Servidor
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

ALUNOS = [
    ("Ana Beatriz Ferreira", "F", dt.date(2016, 4, 12), "52998224725"),
    ("Bruno Henrique Alves", "M", dt.date(2015, 9, 3), "11144477735"),
    ("Carla Souza Lima", "F", dt.date(2016, 1, 27), "12345678909"),
    ("Diego Martins Rocha", "M", dt.date(2015, 11, 8), "39053344705"),
    ("Eduarda Nunes Prado", "F", dt.date(2016, 7, 19), "86288366757"),
]


class Command(BaseCommand):
    help = "Cria dados de demonstração completos (rede, avaliação e frequência)."

    @transaction.atomic
    def handle(self, *args, **options):
        ano = dt.date.today().year
        uf, _ = Estado.objects.get_or_create(sigla="PR", defaults={"nome": "Paraná"})
        municipio, _ = Municipio.objects.get_or_create(
            nome="Curitiba", estado=uf, defaults={"codigo_ibge": "4106902"}
        )
        instituicao, _ = Instituicao.objects.get_or_create(
            sigla="SME",
            defaults={"nome": "Secretaria Municipal de Educação", "municipio": municipio},
        )
        escola, _ = Escola.objects.get_or_create(
            sigla="EMC",
            defaults={
                "instituicao": instituicao,
                "nome": "Escola Municipal Centro",
                "municipio": municipio,
                "codigo_inep": "41000001",
            },
        )
        curso, _ = Curso.objects.get_or_create(
            instituicao=instituicao,
            nome="Ensino Fundamental",
            defaults={"sigla": "EF", "nivel_ensino": "fundamental", "carga_horaria": 800},
        )
        regra, _ = RegraAvaliacao.objects.get_or_create(
            nome="Padrão municipal",
            defaults={
                "tipo_media": "aritmetica",
                "nota_maxima": Decimal("10.00"),
                "media_aprovacao": Decimal("6.00"),
                "media_recuperacao": Decimal("5.00"),
                "percentual_frequencia": 75,
                "casas_decimais": 1,
            },
        )
        serie, _ = Serie.objects.get_or_create(
            curso=curso,
            nome="1º Ano",
            defaults={
                "etapa": 1,
                "carga_horaria": 800,
                "idade_inicial": 6,
                "idade_final": 7,
                "regra_avaliacao": regra,
            },
        )
        if serie.regra_avaliacao_id != regra.id:
            serie.regra_avaliacao = regra
            serie.save(update_fields=["regra_avaliacao"])

        matematica, _ = Disciplina.objects.get_or_create(
            instituicao=instituicao, nome="Matemática", defaults={"sigla": "MAT", "carga_horaria": 200}
        )
        portugues, _ = Disciplina.objects.get_or_create(
            instituicao=instituicao, nome="Português", defaults={"sigla": "POR", "carga_horaria": 240}
        )
        turma, _ = Turma.objects.get_or_create(
            escola=escola,
            nome="1º Ano A",
            ano=ano,
            defaults={"serie": serie, "turno": "matutino", "capacidade": 30},
        )

        ano_letivo, _ = AnoLetivo.objects.get_or_create(
            instituicao=instituicao,
            ano=ano,
            defaults={"data_inicio": dt.date(ano, 2, 2), "data_fim": dt.date(ano, 12, 18)},
        )
        calendario, _ = Calendario.objects.get_or_create(
            ano_letivo=ano_letivo, escola=escola, nome="Calendário 2026"
        )
        inicio = dt.date(ano, 2, 2)
        for dia in range(0, 60):
            data = inicio + dt.timedelta(days=dia)
            if data.weekday() >= 5:
                continue
            CalendarioDia.objects.get_or_create(
                calendario=calendario, data=data, defaults={"tipo": "letivo"}
            )

        periodos = []
        for ordem, nome in enumerate(["1º Bimestre", "2º Bimestre", "3º Bimestre", "4º Bimestre"], start=1):
            periodo, _ = PeriodoAvaliacao.objects.get_or_create(
                ano_letivo=ano_letivo,
                ordem=ordem,
                defaults={
                    "nome": nome,
                    "data_inicio": dt.date(ano, 2 + (ordem - 1) * 2, 1),
                    "data_fim": dt.date(ano, 3 + (ordem - 1) * 2, 28),
                },
            )
            periodos.append(periodo)

        pessoa_professor, _ = Pessoa.objects.get_or_create(
            cpf="01370154962",
            defaults={"nome": "Professor Exemplo", "sexo": "M", "municipio": municipio},
        )
        servidor, _ = Servidor.objects.get_or_create(
            pessoa=pessoa_professor,
            defaults={"cargo": CargoServidor.PROFESSOR, "escola": escola},
        )
        servidor.disciplinas.set([matematica, portugues])

        alocacoes = []
        for disciplina, carga in ((matematica, 200), (portugues, 240)):
            alocacao, _ = TurmaDisciplina.objects.get_or_create(
                turma=turma,
                disciplina=disciplina,
                defaults={"professor": servidor, "carga_horaria": carga},
            )
            alocacoes.append(alocacao)

        usuarios = [
            ("admin@example.com", "Administrador", PerfilUsuario.ADMINISTRADOR, None, True),
            ("gestor@example.com", "Gestor Escolar", PerfilUsuario.GESTOR, escola, False),
            ("secretaria@example.com", "Secretaria Escolar", PerfilUsuario.SECRETARIA, escola, False),
            ("professor@example.com", "Professor Exemplo", PerfilUsuario.PROFESSOR, escola, False),
            ("consulta@example.com", "Perfil Consulta", PerfilUsuario.CONSULTA, escola, False),
        ]
        for email, nome, perfil, escola_vinculo, superusuario in usuarios:
            if not User.objects.filter(email=email).exists():
                if superusuario:
                    user = User.objects.create_superuser(
                        email=email, password="senha-forte-123", nome_completo=nome,
                        perfil=perfil, escola=escola_vinculo,
                    )
                else:
                    user = User.objects.create_user(
                        email=email, password="senha-forte-123", nome_completo=nome,
                        perfil=perfil, escola=escola_vinculo,
                    )
                if perfil == PerfilUsuario.PROFESSOR:
                    user.servidor = servidor
                    user.save(update_fields=["servidor"])
                self.stdout.write(f"  usuario criado: {user.email}")

        turma_inicio = dt.date(ano, 2, 2)
        for indice, (nome, sexo, nascimento, cpf) in enumerate(ALUNOS):
            pessoa, _ = Pessoa.objects.get_or_create(
                cpf=cpf,
                defaults={
                    "nome": nome,
                    "sexo": sexo,
                    "data_nascimento": nascimento,
                    "municipio": municipio,
                    "email": f"aluno{indice + 1}@example.com",
                },
            )
            aluno, _ = Aluno.objects.get_or_create(pessoa=pessoa)
            if indice == 0:
                deficiencia, _ = Deficiencia.objects.get_or_create(
                    nome="Baixa visão", defaults={"codigo_censo": "03"}
                )
                aluno.deficiencias.add(deficiencia)

            matricula, criada = Matricula.objects.get_or_create(
                aluno=aluno,
                ano=turma.ano,
                defaults={
                    "escola": escola,
                    "serie": serie,
                    "curso": curso,
                    "data_matricula": dt.date(ano, 2, 1),
                },
            )
            if criada:
                MatriculaTurma.objects.create(
                    matricula=matricula, turma=turma, data_enturmacao=dt.date(ano, 2, 5)
                )

            for posicao, periodo in enumerate(periodos):
                for deslocamento, alocacao in enumerate(alocacoes):
                    valor = Decimal(str(6 + ((indice + posicao + deslocamento) % 4))).quantize(Decimal("0.1"))
                    Nota.objects.get_or_create(
                        matricula=matricula,
                        turma_disciplina=alocacao,
                        periodo=periodo,
                        tipo=TipoNota.NORMAL,
                        defaults={"valor": valor},
                    )

            for dia in range(10):
                data = turma_inicio + dt.timedelta(days=dia)
                Frequencia.objects.get_or_create(
                    matricula=matricula,
                    data=data,
                    defaults={"turma": turma, "presente": not (dia == 3 and indice % 2 == 0)},
                )

        self.stdout.write(self.style.SUCCESS("Dados de demonstração prontos."))
        self.stdout.write("Login: admin@example.com / senha-forte-123")
