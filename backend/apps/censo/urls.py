from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ExportacaoCensoViewSet

router = DefaultRouter()
router.register("censo/exportacoes", ExportacaoCensoViewSet, basename="exportacao-censo")

urlpatterns = [path("", include(router.urls))]
