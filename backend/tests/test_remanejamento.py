import datetime as dt

import pytest

from apps.enrollments.models import MatriculaTurma

pytestmark = pytest.mark.django_db


def test_remaneja_para_outra_turma(autenticado, matricula, enturmado, turma, serie):
    from apps.schools.models import Turma

    nova = Turma.objects.create(escola=turma.escola, serie=serie, nome="1º Ano B", ano=2026, capacidade=30)
    resposta = autenticado.post(
        f"/api/v1/matriculas/{matricula.pk}/remanejar/", {"turma": nova.id}, format="json"
    )
    assert resposta.status_code == 201, resposta.data
    assert resposta.data["turma"] == nova.id
    assert resposta.data["sequencial"] == 2
    enturmado.refresh_from_db()
    assert enturmado.ativo is False
    assert MatriculaTurma.objects.filter(matricula=matricula, ativo=True).count() == 1


def test_remanejar_respeita_capacidade(autenticado, matricula, enturmado, turma):
    from apps.people.models import Aluno, Pessoa
    from apps.schools.models import Turma

    cheia = Turma.objects.create(
        escola=turma.escola, serie=turma.serie, nome="Cheia", ano=2026, capacidade=1
    )
    outra_pessoa = Pessoa.objects.create(nome="Outro Aluno")
    from apps.enrollments.models import Matricula

    outra = Matricula.objects.create(
        aluno=Aluno.objects.create(pessoa=outra_pessoa),
        escola=cheia.escola,
        serie=cheia.serie,
        curso=cheia.serie.curso,
        ano=2026,
        data_matricula=dt.date(2026, 2, 1),
    )
    MatriculaTurma.objects.create(matricula=outra, turma=cheia, data_enturmacao=dt.date(2026, 2, 2))

    resposta = autenticado.post(
        f"/api/v1/matriculas/{matricula.pk}/remanejar/", {"turma": cheia.id}, format="json"
    )
    assert resposta.status_code == 400
    assert "vagas" in str(resposta.data).lower()


def test_reclassifica_para_outra_serie(autenticado, matricula, enturmado, curso):
    from apps.schools.models import Serie

    nova = Serie.objects.create(curso=curso, nome="2º Ano", etapa=2)
    resposta = autenticado.post(
        f"/api/v1/matriculas/{matricula.pk}/reclassificar/",
        {"serie": nova.id, "observacao": "Avanço de série"},
        format="json",
    )
    assert resposta.status_code == 200, resposta.data
    matricula.refresh_from_db()
    enturmado.refresh_from_db()
    assert matricula.serie_id == nova.id
    assert "Reclassificado" in matricula.observacao
    assert enturmado.ativo is False
