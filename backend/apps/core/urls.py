from django.urls import path

from .views import VersionView, health

urlpatterns = [
    path("health/", health, name="health"),
    path("version/", VersionView.as_view(), name="version"),
]
