from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MatriculaTurmaViewSet, MatriculaViewSet

router = DefaultRouter()
router.register("matriculas", MatriculaViewSet, basename="matricula")
router.register("enturmacoes", MatriculaTurmaViewSet, basename="enturmacao")

urlpatterns = [path("", include(router.urls))]
