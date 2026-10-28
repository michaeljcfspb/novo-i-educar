from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import FrequenciaViewSet

router = DefaultRouter()
router.register("frequencias", FrequenciaViewSet, basename="frequencia")

urlpatterns = [path("", include(router.urls))]
