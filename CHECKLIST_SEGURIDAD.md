# Checklist de seguridad pre-producción

Revisa esto ANTES de dar acceso real a la PyME piloto. Esta version
refleja el estado actual del proyecto (servidor de pruebas ya
convertido a produccion, ver PRODUCCION.md).

## Estado actual (resumen)

- [x] HTTPS real via sslip.io + Let's Encrypt (interino, hasta que
      compres un dominio propio — ver PRODUCCION.md paso 8).
- [x] 2FA obligatorio en el admin (`OTP_ADMIN_ENFORCED = True` en
      `config/settings/prod.py`). PENDIENTE: confirmar que enrolaste tu
      dispositivo (PRODUCCION.md paso 6) — si no, quedas fuera del admin.
- [ ] **CRITICO, sin resolver todavia:** backups fuera del servidor.
      Los respaldos automaticos diarios existen (`docker-compose.prod.yml`
      servicio `backup`), pero solo viven DENTRO del mismo servidor. No
      cargues datos reales de empleados de la PyME piloto hasta tener
      esto resuelto (ver seccion 7).
- [ ] Dominio propio: sigues sin uno. Migrar de sslip.io a un dominio
      real es necesario antes de que esto se vea profesional para un
      cliente y antes de poder enviar campañas reales (Fase 2, requiere
      SPF/DKIM/DMARC que sslip.io no permite configurar).

## 1. Antes de crear el servidor / al contratarlo

- [ ] Elige un proveedor que soporte snapshots/backups a nivel de
      infraestructura además de tus propios backups de BD.
- [ ] Habilita firewall a nivel de proveedor (además del del SO): solo
      80/443 abiertos al publico; 22 (SSH) restringido a tu IP si es
      posible, o con `fail2ban`.
- [ ] Crea un usuario no-root para operar el servidor; deshabilita
      login SSH por contraseña (solo llave publica).

## 2. Variables de entorno y secretos

- [ ] Genera un `DJANGO_SECRET_KEY` real y unico (nunca el de
      `.env.example`) — por ejemplo con
      `python -c "import secrets; print(secrets.token_urlsafe(64))"`.
- [ ] Contraseña de PostgreSQL fuerte y distinta a cualquier otra que uses.
- [ ] El archivo `.env` real NUNCA se sube a un repositorio (ya esta en
      `.gitignore`) ni se comparte por correo/chat sin cifrar.
- [ ] Si en algun momento un secreto se expone (se sube por error a un
      repo, se comparte mal), rotalo de inmediato — no basta con
      borrarlo del historial.

## 3. Configuracion de Django (`config/settings/prod.py`)

- [x] `DEBUG = False`.
- [ ] `DJANGO_ALLOWED_HOSTS` con tus hostnames reales de sslip.io (o tu
      dominio cuando lo tengas), nunca `*`.
- [x] `SECURE_SSL_REDIRECT`, cookies `Secure`/`HttpOnly` ya configurado.
- [ ] Sube `SECURE_HSTS_SECONDS` de 3600 a 31536000 (un año) solo
      despues de confirmar que HTTPS funciona de forma estable por al
      menos una semana.

## 4. Dominio y TLS

- [x] Certificado TLS valido via Let's Encrypt/certbot, usando sslip.io
      como dominio interino (`scripts/init_letsencrypt.sh`).
- [ ] Dominio propio registrado y DNS apuntando al servidor — pendiente.
- [ ] Subdominio SEPARADO para el envio de simulacros (Fase 2), con sus
      propios registros SPF, DKIM y DMARC — requiere dominio propio,
      no aplica todavia con sslip.io. Ver ARCHITECTURE.md seccion 7.

## 5. Autenticacion y datos de empleados

- [x] 2FA (`django-otp`) disponible y exigido en el admin de produccion.
      Enrolar cada cuenta `superadmin`/`admin_pyme` con
      `crear_dispositivo_2fa` + `confirmar_dispositivo_2fa` ANTES de
      darle acceso (ver PRODUCCION.md paso 6).
- [ ] Confirma que `consentimiento_explicito` de cada `Campana` quede
      registrado y no se pueda editar sin dejar rastro en auditoria.
- [ ] Verifica que ningun endpoint exponga `cuerpo_final` de mensajes u
      otros datos de empleados a un rol que no deberia verlos
      (revisar permisos de cada ViewSet antes de agregar mas).
- [ ] Nunca almacenes contraseñas/credenciales reales que un empleado
      "capturado" haya ingresado en una pagina de simulacro (Fase 2) —
      registra unicamente que ocurrio el evento, no el valor ingresado.

## 6. Dependencias y codigo

- [ ] Antes de cada despliegue: `make audit` (bandit + pip-audit) —
      revisa cualquier hallazgo antes de ignorarlo.
- [ ] Manten Django y dependencias actualizadas — suscribete a los
      avisos de seguridad de Django (djangoproject.com/weblog/) o
      revisa `pip-audit` periodicamente (ej. semanalmente).
- [ ] No agregues dependencias nuevas sin revisar minimamente su
      mantenimiento (ultima version, issues abiertos de seguridad).

## 7. Backups y continuidad — CRITICO, PENDIENTE

- [x] Respaldo automatico diario de Postgres dentro del servidor
      (`docker-compose.prod.yml` servicio `backup`).
- [ ] **Copiar los backups FUERA del servidor** (bucket S3-compatible,
      otro servidor). Confirmaste que todavia no tienes donde — hasta
      resolver esto, considera cualquier dato cargado como "en riesgo"
      si el servidor se pierde. No cargues datos reales de empleados de
      la PyME piloto sin esto resuelto, o al menos sin copiar backups a
      tu computadora manualmente cada pocos dias mientras tanto.
- [ ] Haz al menos una prueba real de restauracion (no solo de backup)
      antes de tener datos reales de clientes que no puedas perder.

## 8. Monitoreo (nivel basico acordado)

- [ ] Revisa `docker compose -f docker-compose.prod.yml logs` periodicamente
      o configura un cron simple que te avise si algun contenedor se cayo.
- [ ] Cuando el presupuesto lo permita: activa `SENTRY_DSN` en `.env`
      (ya esta soportado en `prod.py`) para enterarte de errores en
      produccion sin tener que revisar logs manualmente.

## 9. Legal (no tecnico, pero bloqueante para vender)

- [ ] Aviso de privacidad conforme a la LFPDPPP para los datos de
      empleados que procesa la plataforma (nombre, correo, telefono,
      resultados de simulacros).
- [ ] Contrato/acuerdo con cada PyME cliente que deje explicito el
      consentimiento para ejecutar simulacros sobre su personal — esto
      es ademas del check tecnico `consentimiento_explicito` en el codigo.
- [ ] Si vas a procesar datos de una PyME como "encargado" (tu
      procesas, ellos son responsables de los datos), considera un
      acuerdo de encargo de tratamiento de datos.

Este ultimo punto es orientacion general, no asesoria legal — antes de
firmar contratos con clientes reales, conviene una revision por
alguien con experiencia en proteccion de datos en Mexico.
