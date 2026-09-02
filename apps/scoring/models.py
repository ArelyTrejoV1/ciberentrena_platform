from django.db import models

from apps.campaigns.models import PerfilEmpleado


class ScoreRiesgo(models.Model):
    """Última probabilidad de riesgo calculada para un empleado. Se
    recalcula periódicamente (Celery Beat) con datos reales de
    tracking en cuanto exista (Fase 2); por ahora se alimenta del
    histórico sintético documentado en apps/scoring/simulador_historico.py."""

    empleado = models.OneToOneField(PerfilEmpleado, on_delete=models.CASCADE, related_name="score_riesgo")
    probabilidad = models.FloatField(help_text="0.0 a 1.0 — probabilidad de caer en un simulacro.")
    calculado_en = models.DateTimeField(auto_now=True)
    version_modelo = models.CharField(max_length=50, default="baseline-logreg-v1")

    class Meta:
        ordering = ["-probabilidad"]

    def __str__(self):
        return f"{self.empleado} — {self.probabilidad:.1%}"
