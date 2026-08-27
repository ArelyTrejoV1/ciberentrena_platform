from django.contrib import admin

from .models import ScoreRiesgo


@admin.register(ScoreRiesgo)
class ScoreRiesgoAdmin(admin.ModelAdmin):
    list_display = ("empleado", "probabilidad", "version_modelo", "calculado_en")
    list_filter = ("version_modelo",)
    ordering = ("-probabilidad",)
