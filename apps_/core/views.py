from django.db import connection
from django.http import JsonResponse


def healthz(request):
    """Endpoint simple para que Docker/monitoreo confirmen que la app
    responde y que la conexión a la base de datos funciona. No expone
    ningún dato sensible."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_ok = True
    except Exception:
        db_ok = False

    status = 200 if db_ok else 503
    return JsonResponse({"status": "ok" if db_ok else "error", "db": db_ok}, status=status)
