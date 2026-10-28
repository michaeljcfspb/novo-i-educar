from django.urls import path

from .views import BoletimView, DocumentosView, FrequenciaView, PerfilView

urlpatterns = [
    path("portal/perfil/", PerfilView.as_view(), name="portal-perfil"),
    path("portal/boletim/", BoletimView.as_view(), name="portal-boletim"),
    path("portal/frequencia/", FrequenciaView.as_view(), name="portal-frequencia"),
    path("portal/documentos/", DocumentosView.as_view(), name="portal-documentos"),
]
