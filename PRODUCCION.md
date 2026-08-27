# Convertir el servidor de pruebas a producción real

Este documento continúa donde termina `DEPLOYMENT.md`: mismo servidor,
pero ahora en modo producción (HTTPS real, `docker-compose.prod.yml`,
2FA obligatorio en el admin). Como todavía no tienes un dominio propio,
usamos **sslip.io** para obtener un certificado TLS real y válido sin
comprar nada — cuando compres un dominio, el cambio es de un par de
variables (ver el final de este documento).

## 0 — Qué es sslip.io y por qué es válido para producción

sslip.io es un servicio de DNS público gratuito: cualquier hostname con
el formato `algo.TU-IP-CON-GUIONES.sslip.io` resuelve automáticamente a
esa IP — no hace falta registrar nada ni configurar DNS tú misma. Como
SÍ es un dominio real y resoluble públicamente, Let's Encrypt puede
emitir un certificado TLS válido de verdad para él (a diferencia de un
certificado autofirmado, que los navegadores marcan como inseguro).

Es una solución **interina**, no el destino final: no puedes agregar
registros SPF/DKIM/DMARC sobre un dominio que no es tuyo (necesario más
adelante para el envío de campañas de Fase 2), y no se ve profesional
para dárselo a un cliente a largo plazo. Pero para tener HTTPS real
YA, mientras consigues un dominio, funciona perfectamente.

**Calcula tu hostname:** toma tu IP pública y cambia los puntos por
guiones, y agrégale `.sslip.io`. Ejemplo, si tu IP fuera `203.0.113.10`:

```
Dominio público:        203-0-113-10.sslip.io
Dominio del tenant piloto: pyme-piloto.203-0-113-10.sslip.io
```

(Ambos con la MISMA IP al final — sslip.io soporta subdominios
arbitrarios delante de la IP, todos resuelven al mismo servidor.)

Anota estos dos hostnames — los vas a usar varias veces en los pasos
siguientes. En esta guía los llamamos `TU_HOST_PUBLICO` y
`TU_HOST_PILOTO`.

## 1 — Bajar el entorno de pruebas

En el servidor:

```bash
cd ~/ciberentrena_platform
docker compose down
```

(Esto NO borra tus datos — el volumen de Postgres persiste. Si quieres
partir de una base de datos limpia para producción, puedes borrar el
volumen con `docker compose down -v`, pero no es necesario.)

## 2 — Actualizar `.env` para producción

```bash
nano .env
```

Cambia/agrega estas líneas:

```bash
DJANGO_SETTINGS_MODULE=config.settings.prod
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=TU_HOST_PUBLICO,TU_HOST_PILOTO

# Si vas a tener un frontend separado más adelante, descomenta y ajusta:
# CORS_ALLOWED_ORIGINS=https://TU_HOST_PUBLICO

CERTBOT_EMAIL=tu-correo-real@ejemplo.com
CERTBOT_DOMINIOS="TU_HOST_PUBLICO TU_HOST_PILOTO"
CERTBOT_DOMINIOS_PRIMARIO=TU_HOST_PUBLICO
```

Reemplaza `TU_HOST_PUBLICO` y `TU_HOST_PILOTO` por los hostnames reales
que calculaste en el paso 0 (sin los símbolos `<>`).

También, si no lo hiciste al principio, genera valores reales para:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
# pega el resultado en DJANGO_SECRET_KEY
```

Y usa una `POSTGRES_PASSWORD` fuerte y distinta a la que usaste en pruebas.

## 3 — Emitir el certificado TLS real

Dale permiso de ejecución al script (solo la primera vez):

```bash
chmod +x scripts/init_letsencrypt.sh
```

**Recomendado: primero en modo de prueba**, para validar que todo el
flujo funciona sin gastar tu cuota real de Let's Encrypt (que es
limitada por semana):

```bash
STAGING=1 ./scripts/init_letsencrypt.sh
```

Si termina sin errores, repite SIN la variable `STAGING` para obtener
el certificado real:

```bash
./scripts/init_letsencrypt.sh
```

Este script hace todo el proceso solo (certificado temporal → arranca
nginx → pide el certificado real → recarga nginx). Al final te dirá
"Listo" con la URL para verificar.

## 4 — Levantar producción completa

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps
```

Todos los servicios (`db`, `redis`, `web`, `worker`, `beat`, `nginx`,
`certbot`, `backup`) deberían mostrarse corriendo.

Verifica desde el propio servidor:

```bash
curl -k https://localhost/healthz/
```

Y desde tu navegador, ya SIN necesitar túnel SSH (ahora sí es HTTPS
real):

```
https://TU_HOST_PUBLICO/healthz/
```

## 5 — Comandos de arranque (equivalentes a los de pruebas, ahora en prod)

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py bootstrap_tenants --piloto --dominio-publico=TU_HOST_PUBLICO --dominio-piloto=TU_HOST_PILOTO

docker compose -f docker-compose.prod.yml exec web python manage.py tenant_command createsuperuser --schema=pyme_piloto

docker compose -f docker-compose.prod.yml exec web python manage.py tenant_command cargar_plantillas --schema=pyme_piloto

docker compose -f docker-compose.prod.yml exec web python manage.py tenant_command generar_campana_demo --schema=pyme_piloto

docker compose -f docker-compose.prod.yml exec web python manage.py tenant_command entrenar_modelo_riesgo --schema=pyme_piloto
```

## 6 — Activar 2FA (obligatorio antes de dar acceso a la PyME piloto)

En producción, el admin de Django YA exige 2FA verificado
(`OTP_ADMIN_ENFORCED = True` en `config/settings/prod.py`). Esto
significa que **si no enrolas un dispositivo ahora, quedarás bloqueada
del admin** en cuanto intentes entrar. Hazlo antes de cerrar esta sesión:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py tenant_command crear_dispositivo_2fa --schema=pyme_piloto --username=TU_USUARIO
```

Esto imprime una URL `otpauth://` y guarda un QR en `/tmp/qr_2fa_TU_USUARIO.png`
dentro del contenedor. Cópialo a tu máquina para escanearlo:

```bash
docker compose -f docker-compose.prod.yml cp web:/tmp/qr_2fa_TU_USUARIO.png .
```

Ábrelo, escanéalo con Google Authenticator/Authy/1Password, y confirma
con el código de 6 dígitos que te muestre la app:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py tenant_command confirmar_dispositivo_2fa --schema=pyme_piloto --username=TU_USUARIO --token=123456
```

Repite esto para cada cuenta `admin_pyme`/superadmin que vaya a usar el
admin.

## 7 — Pendiente crítico antes de cargar datos reales de empleados

Confirmaste que **todavía no tienes dónde guardar los backups fuera
del servidor**. El servicio `backup` de `docker-compose.prod.yml` ya
genera respaldos diarios DENTRO del servidor (`/backups` en el volumen
`backups_data`), pero eso no te protege si el servidor se pierde
(borrado accidental, falla del proveedor, etc.).

Antes de cargar datos reales de empleados de la PyME piloto, como
mínimo:

```bash
# Copia manual periódica a tu propia computadora, mientras no automatices algo mejor
docker compose -f docker-compose.prod.yml exec backup ls /backups
docker compose -f docker-compose.prod.yml cp backup:/backups/ciberentrena_XXXXXXXX.sql.gz .
```

Cuando tengas un bucket S3-compatible o similar, dímelo y ajustamos
`scripts/backup_db.sh` para que suba ahí automáticamente.

## 8 — Cuando compres un dominio propio

No hay que rehacer nada de esto desde cero:

1. Apunta el registro DNS `A` de tu dominio a la IP del servidor.
2. Actualiza en `.env`: `DJANGO_ALLOWED_HOSTS`, `CERTBOT_DOMINIOS`,
   `CERTBOT_DOMINIOS_PRIMARIO` con el dominio real.
3. Corre de nuevo `./scripts/init_letsencrypt.sh` (pedirá un certificado
   nuevo para el dominio real).
4. `docker compose -f docker-compose.prod.yml up -d` para que todo
   recargue con los valores nuevos.
5. Ahí sí, define un subdominio separado (ej. `campanas.tudominio.mx`)
   para el envío de simulacros de Fase 2, con sus propios SPF/DKIM/DMARC
   — ver `ARCHITECTURE.md` sección 7.
