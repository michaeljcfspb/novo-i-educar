from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ImportacaoViewSet, WebhookViewSet

router = DefaultRouter()
router.register("importacoes", ImportacaoViewSet, basename="importacao")
router.register("webhooks", WebhookViewSet, basename="webhook")

urlpatterns = [path("", include(router.urls))]
