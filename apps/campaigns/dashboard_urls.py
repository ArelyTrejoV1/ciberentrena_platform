from django.urls import path

from . import dashboard

app_name = "dashboard"

urlpatterns = [
    path("", dashboard.lista_campanas, name="lista"),
    path("comparativo/", dashboard.comparativo_rondas, name="comparativo"),
    path("<int:campana_id>/", dashboard.detalle_campana, name="detalle"),
]
