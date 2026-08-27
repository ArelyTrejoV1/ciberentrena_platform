"""
Modelos de campañas de simulacro. Viven en el schema de cada tenant
(TENANT_APPS) — los datos de una PyME nunca son visibles para otra.

Esta app reemplaza, con modelos de base de datos reales, al prototipo
de Fase 1 (generator.py + data/plantillas_mx.json + logs/*.csv).
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class PerfilEmpleado(models.Model):
    """Datos del empleado relevantes para elegir/personalizar simulacros
    y para el modelo de scoring. Separado de Usuario (auth) para no
    mezclar credenciales con datos de RH."""

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfil_empleado"
    )
    departamento = models.CharField(max_length=100)
    puesto = models.CharField(max_length=100, blank=True)
    antiguedad_meses = models.PositiveIntegerField(default=0)
    capacitaciones_previas = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.usuario} — {self.departamento}"


class PlantillaPhishing(models.Model):
    CANAL_EMAIL = "email"
    CANAL_SMS = "sms"
    CANAL_WHATSAPP = "whatsapp"
    CANAL_CHOICES = [
        (CANAL_EMAIL, "Correo electrónico"),
        (CANAL_SMS, "SMS"),
        (CANAL_WHATSAPP, "WhatsApp"),
    ]

    DIFICULTAD_BAJO = "bajo"
    DIFICULTAD_MEDIO = "medio"
    DIFICULTAD_ALTO = "alto"
    DIFICULTAD_CHOICES = [
        (DIFICULTAD_BAJO, "Bajo"),
        (DIFICULTAD_MEDIO, "Medio"),
        (DIFICULTAD_ALTO, "Alto"),
    ]

    clave = models.SlugField(max_length=80, unique=True)
    canal = models.CharField(max_length=20, choices=CANAL_CHOICES)
    categoria = models.CharField(max_length=50)
    dificultad = models.CharField(max_length=20, choices=DIFICULTAD_CHOICES)
    asunto = models.CharField(max_length=200, blank=True)
    cuerpo = models.TextField(help_text="Usa {variable} para los campos a personalizar.")
    variables = models.JSONField(default=list, blank=True)
    senales_alerta = models.JSONField(default=list, blank=True)
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ["categoria", "dificultad"]

    def __str__(self):
        return f"{self.clave} ({self.canal}/{self.dificultad})"


class Campana(models.Model):
    nombre = models.CharField(max_length=150)
    creada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="campanas_creadas"
    )
    consentimiento_explicito = models.BooleanField(
        default=False,
        help_text="Debe ser True para poder generar/enviar mensajes. Requisito ético "
                   "y de mitigación de riesgo del proyecto — no editable desde el admin sin auditoría.",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_envio = models.DateTimeField(null=True, blank=True)

    def clean(self):
        if not self.consentimiento_explicito:
            raise ValidationError(
                "No se puede crear una campaña sin consentimiento explícito de la empresa."
            )

    def __str__(self):
        return self.nombre


class MensajeCampana(models.Model):
    """Un simulacro concreto enviado a un empleado dentro de una campaña.
    'cayo' se actualiza en Fase 2 cuando el módulo de tracking real
    detecte que el empleado hizo clic / ingresó datos."""

    campana = models.ForeignKey(Campana, on_delete=models.CASCADE, related_name="mensajes")
    empleado = models.ForeignKey(PerfilEmpleado, on_delete=models.CASCADE, related_name="mensajes_recibidos")
    plantilla = models.ForeignKey(PlantillaPhishing, on_delete=models.PROTECT)
    asunto_final = models.CharField(max_length=200, blank=True)
    cuerpo_final = models.TextField()
    enviado_en = models.DateTimeField(null=True, blank=True)
    abierto = models.BooleanField(default=False)
    cayo = models.BooleanField(null=True, blank=True, help_text="null = aún sin resultado (Fase 2)")
    fecha_resultado = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["campana", "empleado"])]

    def __str__(self):
        return f"{self.empleado} — {self.plantilla.clave}"
