"""Roteamento raiz: API versionada, Swagger e admin."""
from django.contrib import admin
from django.urls import include, path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from config.spa import spa

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.core.urls")),
    path("api/v1/", include("apps.people.urls")),
    path("api/v1/", include("apps.schools.urls")),
    path("api/v1/", include("apps.enrollments.urls")),
    path("api/v1/", include("apps.assessment.urls")),
    path("api/v1/", include("apps.attendance.urls")),
    path("api/v1/", include("apps.records.urls")),
    path("api/v1/", include("apps.censo.urls")),
    path("api/v1/", include("apps.integrations.urls")),
    path("api/v1/", include("apps.reports.urls")),
    path("api/v1/", include("apps.portal.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    # SPA (React) servido pelo Django no modo local; em produção quem serve é o Nginx.
    re_path(r"^(?P<caminho>(?!api/|admin/|static/|media/).*)$", spa, name="spa"),
]
