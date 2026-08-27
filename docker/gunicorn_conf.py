"""
Configuracion de Gunicorn para produccion. Se referencia con
--config docker/gunicorn_conf.py en el CMD del Dockerfile.

El hook post_worker_init corre en cada proceso worker, DESPUES de que
el worker ya cargo la app (wsgi.py ya corrio get_wsgi_application()),
que es el momento correcto para aplicar el parche de 2FA sobre el
admin de Django (ver apps/core/otp_hook.py).
"""

bind = "0.0.0.0:8000"
workers = 3
timeout = 60


def post_worker_init(worker):
    from apps.core.otp_hook import aplicar_otp_admin_si_corresponde
    aplicar_otp_admin_si_corresponde()
