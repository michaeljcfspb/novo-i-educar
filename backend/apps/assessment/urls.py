from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import NotaViewSet, PeriodoAvaliacaoViewSet, RegraAvaliacaoViewSet

router = DefaultRouter()
router.register("regras-avaliacao", RegraAvaliacaoViewSet, basename="regra-avaliacao")
router.register("periodos-avaliacao", PeriodoAvaliacaoViewSet, basename="periodo-avaliacao")
router.register("notas", NotaViewSet, basename="nota")

urlpatterns = [path("", include(router.urls))]
