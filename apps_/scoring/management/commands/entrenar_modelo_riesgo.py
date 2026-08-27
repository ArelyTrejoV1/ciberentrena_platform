"""
Entrena el modelo baseline de riesgo para el tenant actual.

Por ahora usa el histórico sintético (no hay tracking real todavía —
Fase 2). En cuanto existan suficientes MensajeCampana.cayo != null,
este comando debe cambiarse para entrenar con datos reales (la forma
de las columnas es idéntica, así que risk_model.py no cambia).

Uso:
    python manage.py entrenar_modelo_riesgo
"""

from django.conf import settings
from django.core.management.base import BaseCommand
from django_tenants.utils import get_public_schema_name, connection

from apps.scoring.models import ScoreRiesgo
from apps.scoring.risk_model import RiskScorer
from apps.scoring.simulador_historico import generar_historico_df
from apps.campaigns.models import PerfilEmpleado


class Command(BaseCommand):
    help = "Entrena el modelo de scoring de riesgo con el histórico disponible (sintético por ahora)."

    def handle(self, *args, **options):
        df = generar_historico_df()
        self.stdout.write(f"Histórico sintético: {len(df)} filas, tasa de caída {df['cayo'].mean():.1%}")

        scorer = RiskScorer()
        metricas = scorer.entrenar_desde_dataframe(df)
        self.stdout.write(self.style.SUCCESS(
            f"Accuracy: {metricas['accuracy']:.3f} | ROC-AUC: {metricas['roc_auc']:.3f}"
        ))
        self.stdout.write(metricas["reporte"])

        schema = connection.schema_name
        ruta_modelo = settings.BASE_DIR / "modelos_entrenados" / f"risk_model_{schema}.joblib"
        scorer.guardar(str(ruta_modelo))
        self.stdout.write(f"Modelo guardado en: {ruta_modelo}")

        # Si ya hay empleados reales dados de alta en este tenant, calcula
        # su score usando un escenario "promedio" razonable. Esto es solo
        # una demostración: en Fase 2 el score real se recalcula con los
        # mensajes efectivamente enviados a cada empleado.
        empleados = PerfilEmpleado.objects.all()
        if not empleados.exists():
            self.stdout.write(self.style.WARNING(
                "No hay empleados dados de alta en este tenant todavía — solo se entrenó el modelo."
            ))
            return

        import pandas as pd
        filas = [{
            "departamento": e.departamento, "antiguedad_meses": e.antiguedad_meses,
            "capacitaciones_previas": e.capacitaciones_previas,
            "canal": "email", "categoria": "sat", "dificultad": "medio",
            "hora_envio": "mañana", "dispositivo": "escritorio",
        } for e in empleados]
        proba = scorer.predecir_proba(pd.DataFrame(filas))

        for empleado, p in zip(empleados, proba):
            ScoreRiesgo.objects.update_or_create(
                empleado=empleado, defaults={"probabilidad": float(p)}
            )
        self.stdout.write(self.style.SUCCESS(f"Scores actualizados para {empleados.count()} empleados."))
