# Fase 2 — guía rápida para correr el demo end-to-end

Este documento asume que ya tienes el entorno de pruebas de
`DEPLOYMENT.md` funcionando (docker compose arriba, tenant piloto
creado). Son los pasos para llevarlo del punto donde te quedaste
(23/07, justo antes de generar la campaña demo) hasta tener el flujo
completo: **envío real → tracking → dashboard**, listo para el pitch
del 17 de septiembre.

## 0 — Traer estos cambios a tu copia del proyecto

Estos cambios ya están commiteados en tu repositorio de GitHub
(`ciberentrena_platform`). En tu servidor:

```bash
cd ~/ciberentrena_platform
git pull
```

Si trabajas con `rsync` en vez de git, vuelve a copiar la carpeta completa
(ver Paso 5 de `DEPLOYMENT.md`).

## 1 — Configurar el correo real (Brevo)

1. Crea una cuenta gratis en [brevo.com](https://www.brevo.com) (300
   correos/día gratis, sin tarjeta).
2. Verifica un remitente (Configuración → Expedidores y dominios) —
   con el nivel gratis basta con verificar un correo tuyo, no hace
   falta dominio propio para el piloto.
3. Ve a Configuración → Claves API → SMTP y copia el **Login** y la
   **Clave SMTP** (no es la contraseña de tu cuenta).
4. En tu `.env` del servidor, actualiza:

```bash
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_HOST_USER=<tu-login-smtp-de-brevo>
EMAIL_HOST_PASSWORD=<tu-clave-smtp-de-brevo>
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=<el-correo-que-verificaste-en-brevo>
SITE_URL_SCHEME=http    # http mientras uses el túnel SSH sin dominio; https en producción real
SITE_URL_PORT=8000      # vacío si ya tienes dominio/sslip.io con Nginx delante
```

5. Reinicia el contenedor `web` para que tome el `.env` nuevo:

```bash
docker compose restart web worker beat
```

## 2 — Aplicar las migraciones nuevas

```bash
cd ~/ciberentrena_platform
docker compose exec web python manage.py migrate_schemas --shared
docker compose exec web python manage.py migrate_schemas
```

## 3 — Generar la campaña demo (con correos REALES para poder verla en vivo)

Usa tus propios alias de correo (o los de tu equipo) para los 3
empleados de prueba, así puedes abrir la bandeja de entrada durante el
pitch:

```bash
docker compose exec web python manage.py tenant_command generar_campana_demo \
  --schema=pyme_piloto \
  --correos=rogespino87@gmail.com,arelygguadalupe@gmail.com,emtrejo1327@gmail.com
```
```
docker compose exec web python manage.py tenant_command generar_campana_demo \
  --schema=pyme_piloto \
  --correos=rogespino87@gmail.com,arelygguadalupe@gmail.com,emtrejo1327@gmail.com \
  --nombre="Demo final pitch"
```
(El truco `tu_correo+1@gmail.com` funciona en Gmail: llega a la misma
bandeja que `tu_correo@gmail.com` pero cuentan como direcciones
distintas — perfecto para simular 3 empleados con una sola cuenta.)

Esto reemplaza el paso donde te quedaste — ya no debería fallar.

## 4 — Enviar la campaña de verdad

```bash
docker compose exec web python manage.py tenant_command enviar_campana \
  --schema=pyme_piloto \
  --nombre="Campaña demo — piloto (ronda 1)"
```

Deberías ver `Enviados: 3 | Omitidos: 0 | Fallidos: 0`. Revisa las 3
bandejas de entrada — cada correo trae el enlace "falso" enmascarando
el enlace real de tracking.

## 5 — Dar clic y ver el tracking funcionar

Abre uno de los correos y da clic en el enlace. Deberías ver la página
que imita el engaño; si "envías" ese formulario, te muestra de inmediato
la revelación educativa con las señales de alerta de ese mensaje
específico. Nada de lo que escribas ahí se guarda — solo el hecho de
que llegaste a esa pantalla.

## 6 — Ver el dashboard

Con el túnel SSH del Paso 8 de `DEPLOYMENT.md` abierto:

```
http://localhost:8000/dashboard/
```

Inicia sesión con tu superusuario o con una cuenta `admin_pyme`. Deberías
ver la campaña con su tasa de apertura y de clic, y el detalle por
empleado.

## 7 — (Opcional, para mostrar el "antes/después") Segunda ronda

```bash
docker compose exec web python manage.py tenant_command generar_campana_demo \
  --schema=pyme_piloto --ronda=2 \
  --correos=tu_correo+1@gmail.com,tu_correo+2@gmail.com,tu_correo+3@gmail.com

docker compose exec web python manage.py tenant_command enviar_campana \
  --schema=pyme_piloto --nombre="Campaña demo — piloto (ronda 2)"
```

Da clic en menos correos esta vez (simulando que la capacitación
funcionó) y revisa `http://localhost:8000/dashboard/comparativo/` — ahí
se ve la comparación de tasa de clics entre rondas, que es justo la
métrica que pide el roadmap de Fase 2.

## Qué quedó pendiente (decisión consciente por el tiempo)

- **SMS/WhatsApp (Twilio)**: no implementado — se priorizó tener
  correo funcionando de punta a punta. El modelo y el generador de
  Fase 1 ya soportan esos canales; falta la integración de envío
  (equivalente a `apps/campaigns/sending.py` pero con la API de
  Twilio).
- **Piloto real**: sigues sin una PyME confirmada — el flujo de arriba
  usa la "empresa piloto" de prueba. En cuanto tengas una PyME real,
  dar de alta a sus empleados reales (con su consentimiento) y correr
  los mismos comandos funciona igual.
- **Producción real (HTTPS, 2FA obligatorio)**: sigues en el entorno de
  pruebas (`DEPLOYMENT.md`), no en producción (`PRODUCCION.md`). Para
  el pitch del 17 de septiembre no es necesario — el túnel SSH es
  suficiente y más seguro que abrir el puerto. Antes de dar acceso real
  a empleados de una PyME, sí hay que completar `PRODUCCION.md` +
  `CHECKLIST_SEGURIDAD.md`.
