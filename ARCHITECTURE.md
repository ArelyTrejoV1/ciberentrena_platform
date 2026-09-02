# CiberEntrena — Arquitectura de Plataforma (Fase 1 → producción)

Este documento explica las decisiones de arquitectura para convertir el
prototipo de Fase 1 (generador de simulacros + modelo de scoring) en
una plataforma multi-cliente lista para producción y venta a PyMEs
mexicanas, operada por una sola persona sobre un servidor Linux propio.

## 1. Por qué Django (y no Flask/FastAPI)

Se eligió **Django** por tres razones concretas, dado el contexto del
proyecto (una desarrolladora sola, dato sensible de terceros, camino a
venta comercial):

1. **Seguridad por defecto.** Django trae protección CSRF, escape
   automático de plantillas (mitiga XSS), ORM parametrizado (mitiga
   inyección SQL), hashing de contraseñas configurable, y un sistema
   de sesiones maduro — todo esto sin tener que armarlo ni auditarlo
   a mano. Con Flask o FastAPI, cada una de estas piezas se agrega por
   separado y el riesgo de dejar un hueco (un endpoint sin CSRF, una
   query sin parametrizar) es mayor cuando se trabaja sola.
2. **`django-tenants` para multi-tenancy.** Es la librería más madura
   del ecosistema Python para aislar datos de múltiples clientes
   (esquema-por-tenant en PostgreSQL) y solo existe integración de
   este nivel para Django.
3. **Panel de administración incluido.** El admin de Django cubre de
   entrada gran parte de lo que necesitas para operar manualmente el
   piloto (dar de alta la PyME piloto, ver campañas, revisar
   resultados) sin construir un panel desde cero.

FastAPI sigue siendo una opción válida para un microservicio auxiliar
más adelante (por ejemplo, un endpoint de tracking de alta frecuencia),
pero no como base de toda la plataforma en esta etapa.

## 2. Multi-tenancy: esquema-por-tenant

Cada PyME cliente (**tenant**) tiene su propio *schema* de PostgreSQL.
Todos los tenants comparten la misma base de datos física y el mismo
despliegue de la aplicación, pero Django (vía `django-tenants`)
enruta cada request al schema correcto según el dominio/subdominio de
entrada (`pyme-piloto.ciberentrena.mx`, por ejemplo).

```
PostgreSQL (una sola instancia)
├── schema "public"                 → apps compartidas: tenants, planes, facturación, superadmin
├── schema "pyme_piloto"            → apps de tenant: empleados, campañas, resultados, scoring
├── schema "otra_pyme_cliente"      → (aislado del anterior)
└── ...
```

**Por qué no una tabla compartida con `tenant_id`:** también es válido
y más barato en RAM, pero el aislamiento depende 100% de que *cada*
query en *cada* vista incluya el filtro correcto — un solo `queryset`
sin filtrar filtra datos de una PyME a otra. Con schema-por-tenant, el
aislamiento lo garantiza PostgreSQL a nivel de conexión, no la
disciplina del desarrollador. Para un producto que maneja datos de
empleados de terceros y se va a vender, este nivel de garantía importa
tanto para la seguridad real como para poder decírselo con confianza a
un cliente que pregunte "¿mis datos están separados de los de otras
empresas?".

**Costo de este enfoque:** las migraciones se corren una vez por
schema (django-tenants lo automatiza), y hay un pequeño overhead
operativo. Con un servidor pequeño/mediano y un solo piloto esto no es
un problema; si en el futuro un cliente grande exige aislamiento
físico total (DB dedicada), ese tenant se puede migrar a su propia
instancia sin rediseñar el resto de la plataforma.

## 3. Estructura de apps Django

```
ciberentrena_platform/
├── config/                     # settings, urls raíz, wsgi/asgi, celery.py
│   └── settings/
│       ├── base.py             # todo lo común
│       ├── dev.py              # DEBUG=True, sqlite opcional, correo a consola
│       └── prod.py             # hardening: HTTPS forzado, cookies seguras, etc.
├── apps/
│   ├── tenants/                 # Client (PyME) y Domain — SHARED_APPS (schema public)
│   ├── accounts/                 # Usuario personalizado + roles — SHARED + TENANT
│   ├── campaigns/                 # plantillas, generador, campañas — TENANT_APPS
│   ├── scoring/                    # modelo de riesgo, resultados — TENANT_APPS
│   ├── audit/                       # registro de auditoría — SHARED + TENANT
│   └── core/                         # utilidades comunes, middleware, permisos base
├── static/ , templates/
├── requirements/{base,dev,prod}.txt
├── docker/ (Dockerfile, nginx/, entrypoint.sh)
├── docker-compose.yml            # entorno de desarrollo
├── docker-compose.prod.yml       # entorno de producción
├── scripts/backup_db.sh
└── manage.py
```

Cada app Django es responsable de una sola cosa (principio de
responsabilidad única), lo que en Django es el equivalente práctico a
"MVC ordenado": modelos (`models.py`) + vistas (`views.py`, o
`viewsets.py` si es API) + serializadores/formularios, sin lógica de
negocio mezclada en las plantillas. Esto es lo que da la escalabilidad
a mediano plazo: cuando el equipo crezca, cada app se puede asignar a
una persona distinta sin pisarse.

## 4. Roles y autenticación

Modelo de usuario personalizado (`apps/accounts/models.py`) desde el
día uno (cambiarlo después de tener usuarios reales es doloroso en
Django). Tres roles para esta fase:

- **superadmin**: tú. Vive en el schema `public`, administra clientes
  (altas de PyME), planes, y tiene acceso de soporte a los tenants.
- **admin_pyme**: el contacto de la empresa piloto. Ve el dashboard de
  su propia empresa (resultados, empleados, reportes), nada de otras.
- **empleado**: solo ve su propio progreso de capacitación (Fase 2/3).

Autenticación por sesión (cookies) para el panel web tradicional;
Django REST Framework + JWT (`djangorestframework-simplejwt`, tokens
de vida corta + refresh) si más adelante se construye un frontend
separado (React/Vue) o una app móvil. Contraseñas con **Argon2**
(`django-argon2`, más resistente a fuerza bruta con GPU que el hasher
por defecto de Django). 2FA (`django-otp`) recomendado para
`superadmin` y `admin_pyme` desde el lanzamiento comercial — no es
opcional cuando la cuenta controla datos de empleados de un cliente.

## 5. Tareas en segundo plano: Celery + Redis

El envío de campañas (Fase 2), el cálculo de scoring, y el envío de
reportes por correo **no deben bloquear** la respuesta HTTP. Celery
(con Redis como broker) ejecuta esto de forma asíncrona:

- `campaigns.tasks.enviar_campana`: genera y envía los simulacros de un
  lote sin que el usuario espere en el navegador.
- `scoring.tasks.recalcular_riesgo`: recalcula el score de riesgo por
  empleado periódicamente (Celery Beat, ej. cada noche).
- `audit`: cualquier acción sensible (alta de campaña, cambio de rol,
  exportación de datos) se registra de forma síncrona en el modelo de
  auditoría — esto si debe ser inmediato y confiable, no async.

## 6. Contenedores (Docker)

```
docker-compose.yml (dev)          docker-compose.prod.yml
├── db (postgres:16)              ├── db (postgres:16, volumen persistente + backups)
├── redis                         ├── redis
├── web (Django + runserver)      ├── web (Django + gunicorn, sin DEBUG)
├── worker (celery)               ├── worker (celery, réplicas si el servidor lo permite)
├── beat (celery beat)            ├── beat (celery beat)
└── mailhog (correo de prueba)    ├── nginx (proxy inverso + TLS Let's Encrypt/certbot)
                                   └── backup (cron de pg_dump)
```

Dado que no confirmaste las specs exactas del servidor, el diseño
asume un servidor pequeño/mediano (2-4 GB RAM) y todo corre en un solo
host. Si el servidor termina siendo más grande, escalar es tan simple
como aumentar réplicas de `worker` y ajustar los límites de recursos en
`docker-compose.prod.yml` — no requiere cambiar código.

## 7. Dominio y envío de correo/SMS

Como todavía no tienes dominio: la plataforma está lista para operar
con uno en cuanto lo consigas, pero **no se puede salir a producción
real sin él** (TLS válido y reputación de envío lo requieren). Un
punto que sí es innegociable desde el diseño: el dominio de envío de
simulacros (Fase 2) **debe ser un subdominio separado** del dominio
principal de la plataforma (ej. `campanas.ciberentrena.mx` vs
`app.ciberentrena.mx`), con sus propios registros SPF/DKIM/DMARC. Así,
si algún proveedor de correo marca el subdominio de envíos como
sospechoso (es phishing simulado, después de todo — puede pasar), la
reputación del dominio principal donde vive el panel de clientes no se
ve afectada.

## 8. Observabilidad (nivel básico, como se acordó)

- Logs estructurados (JSON) a stdout — Docker los captura, se pueden
  rotar con `logrotate` o revisar con `docker logs`.
- Respaldo automático diario de PostgreSQL (`pg_dump` vía contenedor
  `backup` + cron), con retención de al menos 7 días y copia fuera del
  servidor (ej. a un bucket S3-compatible económico) — un respaldo que
  vive solo en el mismo servidor no protege contra que el servidor se
  pierda.
- Cuando haya presupuesto: Sentry para captura de errores en
  producción y métricas (Prometheus/Grafana) — documentado como
  siguiente paso, no bloqueante para el piloto.

## 9bis. Fase 2 — envío real, tracking y dashboard

Lo que faltaba (marcado como TODO en el código) para pasar del
prototipo de Fase 1 a una plataforma que realmente envía, mide y
reporta simulacros:

- **`apps/campaigns/sending.py`**: envío real por SMTP (Brevo en el
  piloto). Por cada `MensajeCampana` con `canal=email` y empleado con
  correo registrado, arma un correo HTML: el texto generado en Fase 1
  queda igual, pero el `link_falso_visible` que el empleado VE se
  enmascara con un `<a href>` real apuntando al endpoint de tracking
  (mismo truco que un ataque real), y se agrega un pixel de 1x1 al
  final. SMS/WhatsApp (Twilio) siguen sin implementarse — se priorizó
  tener el flujo completo funcionando con un solo canal a tiempo.
- **`apps/campaigns/tracking.py` + `tracking_urls.py`** (rutas `/t/...`,
  públicas, sin login): `/t/o/<token>.gif` marca `abierto`; `/t/c/<token>/`
  marca `cayo` y muestra una página que imita el engaño (nunca pide
  contraseñas reales) — si el empleado la "envía", se marca
  `dato_ingresado` SIN leer ni guardar lo que escribió, y se le muestra
  de inmediato la revelación educativa con las `señales_alerta` de esa
  plantilla específica. Esto también cumple, de forma económica, la
  parte de "capacitación dirigida a quien cayó" del proyecto original.
- **`apps/campaigns/dashboard.py` + `dashboard_urls.py`** (rutas
  `/dashboard/...`, requieren rol `admin_pyme`/`superadmin`): lista de
  campañas con tasa de apertura/clic, detalle por empleado, y una vista
  comparativa por `ronda` (nuevo campo en `Campana`) para medir
  antes/después de una capacitación, tal como pide el roadmap.
- **`apps/core/site_url.py`**: arma la URL pública del tenant actual a
  partir de su `Dominio` primario — necesario porque el envío real
  puede ocurrir desde una tarea de Celery, que no tiene un `request` del
  que sacar el host.

Tres bugs que bloqueaban esto y se corrigieron en el mismo trabajo:

1. La carpeta del código vivía como `apps_/` en el repo (con `apps/`
   vacía) mientras todo el código importa `apps.algo` — el proyecto no
   podía arrancar. Se renombró `apps_` → `apps`.
2. `Campana.creada_por` no tenía `blank=True`, así que `full_clean()`
   rechazaba una campaña generada por un comando/tarea (sin usuario
   humano) aunque la base de datos sí lo permitía — este era
   exactamente el error donde te quedaste el 23 de julio.
3. `django-debug-toolbar` estaba activo en `INSTALLED_APPS`/`MIDDLEWARE`
   de `dev.py` pero sus URLs nunca se registraron en `config/urls.py` —
   cualquier página en modo desarrollo tronaba con
   `NoReverseMatch('djdt')`. Se agregó el bloque `if settings.DEBUG`
   correspondiente.

## 9. Qué NO se decidió todavía (pendiente de tu servidor real)

Cuando confirmes specs del servidor (RAM/vCPU/distro), ajustamos:
límites de memoria por contenedor en `docker-compose.prod.yml`, número
de workers de Gunicorn/Celery, y si Redis/Postgres corren en el mismo
host o se separan. El scaffold entregado ya trae valores conservadores
por defecto (pensados para 2-4 GB RAM) para que funcione sin ajustes
en un VPS económico.
