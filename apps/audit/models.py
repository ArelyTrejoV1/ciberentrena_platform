"""
Registro de auditoría en base de datos (reemplaza el CSV plano usado
en el prototipo de Fase 1). Queda dentro del schema del tenant, así
que cada PyME solo ve su propia auditoría; el superadmin puede
consultar la del schema public para acciones a nivel plataforma.

Se registra CUALQUIER acción sensible: generación/envío de una
campaña de simulacro, exportación de datos de empleados, cambios de
rol, inicios de sesión fallidos repetidos. Esto es tanto un requisito
de seguridad (trazabilidad si algo sale mal) como de la mitigación de
riesgo definida en el proyecto original ("uso indebido de la
herramienta").
"""

from django.conf import settings
from django.db import models


class RegistroAuditoria(models.Model):
    ACCION_LOGIN_EXITOSO = "login_exitoso"
    ACCION_LOGIN_FALLIDO = "login_fallido"
    ACCION_CAMPANA_GENERADA = "campana_generada"
    ACCION_CAMPANA_ENVIADA = "campana_enviada"
    ACCION_EXPORTACION_DATOS = "exportacion_datos"
    ACCION_CAMBIO_ROL = "cambio_rol"
    ACCION_SIMULACRO_APERTURA = "simulacro_apertura"
    ACCION_SIMULACRO_CLIC = "simulacro_clic"
    ACCION_SIMULACRO_DATO_INGRESADO = "simulacro_dato_ingresado"
    ACCION_CHOICES = [
        (ACCION_LOGIN_EXITOSO, "Login exitoso"),
        (ACCION_LOGIN_FALLIDO, "Login fallido"),
        (ACCION_CAMPANA_GENERADA, "Campaña generada"),
        (ACCION_CAMPANA_ENVIADA, "Campaña enviada"),
        (ACCION_EXPORTACION_DATOS, "Exportación de datos"),
        (ACCION_CAMBIO_ROL, "Cambio de rol"),
        (ACCION_SIMULACRO_APERTURA, "Empleado abrió un simulacro"),
        (ACCION_SIMULACRO_CLIC, "Empleado hizo clic en un simulacro (cayó)"),
        (ACCION_SIMULACRO_DATO_INGRESADO, "Empleado envió datos en la página falsa"),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    accion = models.CharField(max_length=50, choices=ACCION_CHOICES)
    detalle = models.JSONField(default=dict, blank=True)
    ip_origen = models.GenericIPAddressField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado_en"]
        indexes = [models.Index(fields=["accion", "creado_en"])]

    def __str__(self):
        return f"[{self.creado_en:%Y-%m-%d %H:%M}] {self.usuario} — {self.get_accion_display()}"
