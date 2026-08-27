"""
Modelos de multi-tenancy (django-tenants). Cliente = una PyME que
contrató la plataforma; cada Cliente tiene su propio schema de
PostgreSQL, creado/migrado automáticamente por django-tenants al
guardarse con auto_create_schema=True.

Dominio conecta un hostname (ej. "pyme-piloto.ciberentrena.mx", o
"localhost" en dev) con el Cliente correspondiente — así es como
Django decide a qué schema enrutar cada request.
"""

from django.db import models
from django_tenants.models import DomainMixin, TenantMixin


class Cliente(TenantMixin):
    PLAN_PILOTO = "piloto"
    PLAN_BASICO = "basico"
    PLAN_PRO = "pro"
    PLAN_CHOICES = [
        (PLAN_PILOTO, "Piloto (sin costo)"),
        (PLAN_BASICO, "Básico"),
        (PLAN_PRO, "Pro"),
    ]

    nombre_empresa = models.CharField(max_length=200)
    rfc = models.CharField(max_length=13, blank=True)
    contacto_nombre = models.CharField(max_length=150, blank=True)
    contacto_email = models.EmailField(blank=True)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default=PLAN_PILOTO)
    activo = models.BooleanField(default=True)
    fecha_alta = models.DateTimeField(auto_now_add=True)

    # Crea el schema de Postgres automáticamente al guardar por primera vez.
    auto_create_schema = True
    auto_drop_schema = False  # nunca borrar datos de un cliente automáticamente

    def __str__(self):
        return self.nombre_empresa


class Dominio(DomainMixin):
    """Requerido por django-tenants: hostname -> Cliente."""
    pass
