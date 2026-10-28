from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AlunoViewSet, DeficienciaViewSet, PessoaViewSet, ServidorViewSet

router = DefaultRouter()
router.register("pessoas", PessoaViewSet, basename="pessoa")
router.register("alunos", AlunoViewSet, basename="aluno")
router.register("deficiencias", DeficienciaViewSet, basename="deficiencia")
router.register("servidores", ServidorViewSet, basename="servidor")

urlpatterns = [path("", include(router.urls))]
