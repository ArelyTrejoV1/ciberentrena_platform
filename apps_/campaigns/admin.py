from django.contrib import admin

from .models import Campana, MensajeCampana, PerfilEmpleado, PlantillaPhishing


@admin.register(PerfilEmpleado)
class PerfilEmpleadoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "departamento", "puesto", "antiguedad_meses", "capacitaciones_previas")
    list_filter = ("departamento",)


@admin.register(PlantillaPhishing)
class PlantillaPhishingAdmin(admin.ModelAdmin):
    list_display = ("clave", "canal", "categoria", "dificultad", "activa")
    list_filter = ("canal", "categoria", "dificultad", "activa")
    search_fields = ("clave", "categoria")


class MensajeCampanaInline(admin.TabularInline):
    model = MensajeCampana
    extra = 0
    readonly_fields = ("empleado", "plantilla", "asunto_final", "enviado_en", "cayo")
    can_delete = False


@admin.register(Campana)
class CampanaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "creada_por", "consentimiento_explicito", "fecha_creacion", "fecha_envio")
    list_filter = ("consentimiento_explicito",)
    inlines = [MensajeCampanaInline]
    readonly_fields = ("fecha_creacion",)
