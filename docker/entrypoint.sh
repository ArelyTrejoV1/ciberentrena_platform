#!/usr/bin/env bash
set -euo pipefail

# Espera a que Postgres esté listo antes de arrancar (evita crashes en el
# primer boot cuando db aún no aceptó conexiones).
until python -c "
import os, sys, psycopg2
try:
    psycopg2.connect(
        dbname=os.environ['POSTGRES_DB'],
        user=os.environ['POSTGRES_USER'],
        password=os.environ['POSTGRES_PASSWORD'],
        host=os.environ['POSTGRES_HOST'],
        port=os.environ['POSTGRES_PORT'],
    )
except Exception as e:
    print(f'Esperando a Postgres... ({e})')
    sys.exit(1)
"; do
  sleep 2
done

echo "Postgres disponible."

# Solo el servicio 'web' corre migraciones y recolecta estáticos, para que
# no se ejecuten en paralelo desde worker/beat también.
if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
  echo "Aplicando migraciones (todos los tenants + esquema público)..."
  python manage.py migrate_schemas --shared
  python manage.py migrate_schemas
  python manage.py collectstatic --noinput
fi

exec "$@"
