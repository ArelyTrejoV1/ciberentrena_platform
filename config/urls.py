"""URLs que ve un usuario DENTRO de un tenant (una PyME cliente):
login, dashboard, campañas, scoring, API."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("api/campaigns/", include("apps.campaigns.urls")),
    path("api/scoring/", include("apps.scoring.urls")),
    path("healthz/", include("apps.core.urls")),
]
