from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DocumentoViewSet, HistoricoViewSet, TransferenciaViewSet

router = DefaultRouter()
router.register("historicos", HistoricoViewSet, basename="historico")
router.register("transferencias", TransferenciaViewSet, basename="transferencia")
router.register("documentos", DocumentoViewSet, basename="documento")

urlpatterns = [path("", include(router.urls))]
