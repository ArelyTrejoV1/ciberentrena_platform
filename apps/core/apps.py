from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Utilidades compartidas"

    def ready(self):
        from . import admin_log_patch  # noqa: F401 — aplica el parche al importarse
