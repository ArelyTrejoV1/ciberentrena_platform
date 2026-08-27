#!/bin/sh
# Respaldo diario de PostgreSQL (incluye TODOS los schemas/tenants).
# Retiene los últimos 7 días localmente. IMPORTANTE: además de esto,
# copia periódicamente /backups a un almacenamiento fuera del servidor
# (bucket S3-compatible, otro servidor, etc.) — un respaldo que solo
# vive en el mismo servidor no protege si el servidor se pierde.

set -eu

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="/backups/ciberentrena_${TIMESTAMP}.sql.gz"

echo "Generando respaldo: ${FILENAME}"
PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
  -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
  | gzip > "${FILENAME}"

echo "Respaldo completado."

# Borra respaldos con más de 7 días
find /backups -name "ciberentrena_*.sql.gz" -mtime +7 -delete

echo "Respaldos actuales:"
ls -lh /backups
