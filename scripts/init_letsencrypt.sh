#!/usr/bin/env bash
# Emisión del PRIMER certificado TLS real de Let's Encrypt para
# docker-compose.prod.yml. Solo se corre UNA VEZ por servidor (la
# renovación automática ya la hace el servicio "certbot" del propio
# docker-compose.prod.yml). Patrón estándar para nginx+certbot en
# Docker: se necesita un certificado "dummy" primero para que nginx
# pueda arrancar (su config ya referencia rutas de certificado), y
# luego se reemplaza por el real.
#
# Uso (desde la raíz del proyecto, en el servidor):
#   ./scripts/init_letsencrypt.sh
#
# Requiere que en .env estén CERTBOT_EMAIL y CERTBOT_DOMINIOS
# (ver .env.example). El primer dominio de CERTBOT_DOMINIOS determina
# la carpeta del certificado (Let's Encrypt usa el primero como nombre).

set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "No se encontró .env. Copia .env.example a .env y complétalo primero." >&2
  exit 1
fi
set -a
source .env
set +a

if [ -z "${CERTBOT_DOMINIOS:-}" ] || [ -z "${CERTBOT_EMAIL:-}" ]; then
  echo "Faltan CERTBOT_DOMINIOS y/o CERTBOT_EMAIL en .env." >&2
  exit 1
fi

read -r -a DOMINIOS <<< "$CERTBOT_DOMINIOS"
PRIMARIO="${DOMINIOS[0]}"
COMPOSE="docker compose -f docker-compose.prod.yml"

DOMAIN_ARGS=""
for d in "${DOMINIOS[@]}"; do
  DOMAIN_ARGS="$DOMAIN_ARGS -d $d"
done

echo "Dominio(s): ${DOMINIOS[*]}"
echo "Certificado se guardará como: $PRIMARIO"
echo

# Modo de prueba: usa STAGING=1 ./scripts/init_letsencrypt.sh para probar
# el flujo completo sin gastar tu cuota real de Let's Encrypt (los
# certificados de staging no son válidos para navegadores, pero sirven
# para confirmar que todo el proceso funciona antes de pedir el real).
STAGING_ARG=""
if [ "${STAGING:-0}" = "1" ]; then
  echo "MODO STAGING activado (certificado de prueba, no válido para producción real)."
  STAGING_ARG="--staging"
fi

echo "1) Creando certificado temporal (dummy) para que nginx pueda arrancar..."
$COMPOSE run --rm --entrypoint "\
  mkdir -p /etc/letsencrypt/live/$PRIMARIO && \
  openssl req -x509 -nodes -newkey rsa:4096 -days 1 \
    -keyout /etc/letsencrypt/live/$PRIMARIO/privkey.pem \
    -out /etc/letsencrypt/live/$PRIMARIO/fullchain.pem \
    -subj '/CN=localhost'" certbot

echo "2) Arrancando nginx con el certificado temporal..."
$COMPOSE up -d nginx

echo "3) Borrando el certificado temporal..."
$COMPOSE run --rm --entrypoint "rm -rf /etc/letsencrypt/live/$PRIMARIO" certbot

echo "4) Solicitando el certificado REAL a Let's Encrypt..."
$COMPOSE run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    --email $CERTBOT_EMAIL $DOMAIN_ARGS \
    --rsa-key-size 4096 --agree-tos --no-eff-email $STAGING_ARG" certbot

echo "5) Recargando nginx con el certificado real..."
$COMPOSE exec nginx nginx -s reload

echo
echo "Listo. Verifica en el navegador: https://$PRIMARIO"
echo "Si usaste STAGING=1, repite SIN esa variable para obtener el certificado real."
