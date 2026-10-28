from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AnoLetivoViewSet,
    CalendarioViewSet,
    CursoViewSet,
    DisciplinaViewSet,
    EscolaViewSet,
    InstituicaoViewSet,
    SerieViewSet,
    TurmaDisciplinaViewSet,
    TurmaViewSet,
)

router = DefaultRouter()
router.register("instituicoes", InstituicaoViewSet, basename="instituicao")
router.register("escolas", EscolaViewSet, basename="escola")
router.register("cursos", CursoViewSet, basename="curso")
router.register("series", SerieViewSet, basename="serie")
router.register("disciplinas", DisciplinaViewSet, basename="disciplina")
router.register("turmas", TurmaViewSet, basename="turma")
router.register("anos-letivos", AnoLetivoViewSet, basename="ano-letivo")
router.register("calendarios", CalendarioViewSet, basename="calendario")
router.register("turma-disciplinas", TurmaDisciplinaViewSet, basename="turma-disciplina")

urlpatterns = [path("", include(router.urls))]
