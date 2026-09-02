# Guía de despliegue — ambiente de pruebas en tu servidor

Este documento asume que estás partiendo de cero: eliges el servidor,
lo configuras, y despliegas ahí el entorno de **desarrollo/pruebas**
(no producción todavía — sin dominio ni TLS). Cuando consigas un
dominio y quieras dar acceso real a la PyME piloto, usa la sección
"Producción" del `README.md` y repasa `CHECKLIST_SEGURIDAD.md` antes.

Sigue los pasos en orden; cada uno depende del anterior. Los comandos
están pensados para copiar/pegar tal cual en tu terminal.

---

## Paso 0 — Elegir el servidor

**Distribución recomendada: Ubuntu 24.04 LTS.** Es la que tiene más
documentación disponible, el mejor soporte oficial de Docker, y
soporte de seguridad hasta 2029 — importante para no tener que migrar
el sistema operativo a media operación. Si ya tienes experiencia con
Debian o con CentOS/Rocky/Alma, también funcionan (los comandos de
`apt` cambiarían a `dnf`/`yum`), pero esta guía usa Ubuntu.

**Specs mínimas para este ambiente de pruebas:** 1 vCPU / 2 GB RAM
alcanza para levantar Postgres + Redis + Django + Celery en modo dev.
Si puedes conseguir 2 vCPU / 4 GB, mejor margen y menos probabilidad
de que el servidor se quede sin memoria la primera vez que levantes
todo junto.

Cualquier proveedor de VPS que te deje elegir "Ubuntu 24.04 LTS" al
crear el servidor sirve (DigitalOcean, Hetzner, Linode/Akamai, Vultr,
AWS Lightsail, etc. — son solo ejemplos, no hay una opción "correcta").
Al crear el servidor, la mayoría de proveedores te dejan **subir una
llave SSH pública desde el primer momento** — hazlo si puedes, te
ahorra el paso de configurar la llave después.

Anota la **IP pública** de tu servidor; la vas a necesitar en todos los
pasos siguientes (aquí la llamaremos `74.208.166.250`).

---

## Paso 1 — Generar una llave SSH (si no tienes una)

En **tu computadora** (no en el servidor):

```bash
ssh-keygen -t ed25519 -C "arelytrejo@arelytrejo.com"
# Acepta la ruta por default (~/.ssh/id_ed25519), y pon una passphrase si quieres
```

Esto crea dos archivos: `~/.ssh/id_ed25519` (privada, NUNCA la
compartas) y `~/.ssh/id_ed25519.pub` (pública, esta sí se sube al
servidor).

Si tu proveedor no te dejó subir la llave al crear el servidor, cópiala
ahora con:

```bash
ssh-copy-id root@74.208.166.250
```

(te pedirá la contraseña de root que te dio el proveedor por correo/panel).

---

## Paso 2 — Primer acceso y usuario no-root

Conéctate como root la primera vez:

```bash
ssh root@74.208.166.250
```

Una vez dentro del servidor, crea un usuario normal con permisos de
sudo (nunca operes el día a día como root):

```bash
adduser ciberentrena
usermod -aG sudo ciberentrena

# Copia tu llave SSH al nuevo usuario
rsync --archive --chown=ciberentrena:ciberentrena ~/.ssh /home/ciberentrena
```

Abre una **segunda terminal** (deja la de root abierta por si algo
falla) y confirma que puedes entrar con el nuevo usuario:

```bash
ssh ciberentrena@74.208.166.250
```

Si funciona, en la terminal de root desactiva el login por contraseña
y como root directo (endurece el acceso SSH):

```bash
sudo nano /etc/ssh/sshd_config
```

Busca y ajusta estas líneas (quita el `#` si están comentadas):

```
PermitRootLogin no
PasswordAuthentication no
```

Guarda (`Ctrl+O`, `Enter`, `Ctrl+X`) y reinicia SSH:

```bash
sudo systemctl restart ssh
```

Desde ahora, conéctate siempre como `ciberentrena@74.208.166.250`, ya
no como root.

---

## Paso 3 — Firewall básico

```bash
sudo apt update && sudo apt install -y ufw
sudo ufw allow OpenSSH
sudo ufw enable   # confirma con "y"
sudo ufw status
```

Por ahora solo SSH (22) está permitido. Los puertos de la app (8000,
etc.) los abriremos más adelante SOLO si decides exponerlos
directamente — la opción recomendada (Paso 6) no requiere abrir nada
más.

---

## Paso 4 — Instalar Docker Engine + Compose

Comandos oficiales de Docker para Ubuntu:

```bash
# Quita versiones viejas si las hubiera (no falla si no existen)
for pkg in docker.io docker-doc docker-compose podman-docker containerd runc; do sudo apt-get remove -y $pkg; done

sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Permite que tu usuario use Docker sin `sudo`:

```bash
sudo usermod -aG docker $USER
```

Cierra sesión SSH y vuelve a entrar para que el cambio de grupo tome
efecto:

```bash
exit
ssh ciberentrena@74.208.166.250
```

Verifica que todo quedó bien:

```bash
docker run hello-world
docker compose version
```

Si ves el mensaje de "Hello from Docker!" y una versión de Compose,
quedó instalado correctamente.

---

## Paso 5 — Llevar el proyecto al servidor

Tienes el proyecto en tu computadora, en la carpeta `ciberentrena_platform/`.
Dos formas de subirlo (elige una):

### Opción A — rsync (más simple si aún no usas Git)

Desde **tu computadora**, en la carpeta que CONTIENE `ciberentrena_platform/`:

```bash
rsync -avz --exclude='.git' --exclude='__pycache__' --exclude='.env' \
  ciberentrena_platform/ ciberentrena@74.208.166.250:~/ciberentrena_platform/
```

### Opción B — Git (recomendado a mediano plazo)

Si ya tienes o vas a crear un repositorio (GitHub/GitLab, puede ser
privado):

```bash
# En tu computadora, dentro de ciberentrena_platform/
git init
git add .
git commit -m "Scaffold inicial de la plataforma"
git remote add origin <URL_DE_TU_REPO>
git push -u origin main
```

```bash
# En el servidor
git clone <URL_DE_TU_REPO> ~/ciberentrena_platform
```

Con Git, actualizar el servidor después es solo `git pull` — más
cómodo que repetir `rsync` cada vez. El `.gitignore` ya está listo
para no subir `.env`, `__pycache__`, backups, etc.

---

## Paso 6 — Configurar el `.env` en el servidor

```bash
cd ~/ciberentrena_platform
cp .env.example .env
nano .env
```

Para este ambiente de pruebas, como mínimo cambia:

- `DJANGO_SECRET_KEY`: genera uno real con
  `python3 -c "import secrets; print(secrets.token_urlsafe(64))"`

  =KoxxHzYCfwyEa7w1zpUcchowEt8w5Y1jrn-sXoo9Uic3Toz2DTt1Z24MlWwGLR_oAQWGD3>


  (puedes correrlo en el propio servidor).
- `POSTGRES_PASSWORD`: una contraseña que no uses en ningún otro lado.


# --- Base de datos (Postgres) ---
POSTGRES_DB=ciberentrena
POSTGRES_USER=ciberentrena
POSTGRES_PASSWORD=Ciberentrena1.
POSTGRES_HOST=db
POSTGRES_PORT=5432



Deja `DJANGO_SETTINGS_MODULE=config.settings.dev` — estamos en modo
pruebas, no producción.

---

## Paso 7 — Levantar el entorno

```bash
cd ~/ciberentrena_platform
docker compose up --build -d
```
<!-- ok arely 27082026 -->
La primera vez tarda varios minutos (construye las imágenes). Verifica
que todo esté corriendo:

```bash
docker compose ps
```

Deberías ver `db`, `redis`, `web`, `worker`, `beat`, `mailhog` como
`running`/`healthy`. Si alguno no arrancó, revisa sus logs (Paso 10).

Confirma que Django responde, desde dentro del propio servidor:

```bash
curl http://localhost:8000/healthz/
# Esperado: {"status": "ok", "db": true}
```

---

## Paso 8 — Acceder desde tu navegador (sin exponer el servidor a internet)

Como todavía no hay dominio ni HTTPS, **no recomiendo abrir el puerto
8000 al público** — sería servir el panel de administración sin TLS,
directamente en internet. La forma segura de verlo desde tu navegador
es un **túnel SSH**, que reutiliza la conexión SSH ya cifrada:

Desde **tu computadora**:

```bash
ssh -L 8000:localhost:8000 -L 8025:localhost:8025 ciberentrena@74.208.166.250
```

Deja esa terminal abierta y abre en tu navegador:

- `http://localhost:8000/admin/` — panel de Django (del servidor real)
- `http://localhost:8025` — bandeja de MailHog (correos de prueba)

Todo el tráfico va cifrado por el túnel SSH aunque la app en sí no
tenga TLS propio — perfectamente adecuado para pruebas internas.

**Si prefieres abrir el puerto directamente** (por ejemplo para
compartirlo rápido con alguien más), hazlo solo temporalmente y
ciérralo después:

```bash
sudo ufw allow 8000/tcp
# ... pruebas ...
sudo ufw delete allow 8000/tcp
```

---

## Paso 9 — Comandos post-arranque (dentro del servidor)

```bash
cd ~/ciberentrena_platform

# Crea el schema public + un tenant piloto de ejemplo
docker compose exec web python manage.py bootstrap_tenants --piloto

# Superusuario para el tenant piloto (te pedirá usuario/correo/contraseña)
# docker compose exec web python manage.py tenant_command createsuperuser --schema=pyme_piloto
# no se xq el de arriba no me funciono
docker exec -it ciberentrena_platform-web-1 python manage.py createsuperuser


#Nombre de usuario: admin
#Dirección de correo electrónico: arelytrejo@arelytrejo.com
#Password:
#Password (again):
#Error: Your passwords didn't match.
#Password:ICELABRA1abc.
#Password (again):
#La contraseña es muy similar a  nombre de usuario.
#La contraseña es muy corta. Debe contener al menos 12 caracteres.
#Esta contraseña es muy común.
#Bypass password validation and create user anyway? [y/N]: y


# Carga el dataset de plantillas de phishing en el tenant piloto
docker compose exec web python manage.py tenant_command cargar_plantillas --schema=pyme_piloto

# Genera una campaña de ejemplo con empleados de prueba
#arely AQUI ME QUEDÉ --- 23072026
docker compose exec web python manage.py tenant_command generar_campana_demo --schema=pyme_piloto

# Entrena el modelo baseline de riesgo (histórico sintético por ahora)
docker compose exec web python manage.py tenant_command entrenar_modelo_riesgo --schema=pyme_piloto
```

Con el túnel SSH del Paso 8 abierto, entra a
`http://localhost:8000/admin/` con el superusuario que creaste y
deberías ver las plantillas, la campaña demo y el score de riesgo
(si diste de alta empleados con `PerfilEmpleado`).

---
<!-- Me quedè aquì no puedo iniciar sesion -->

## Paso 10 — Troubleshooting básico

```bash
# Ver logs de un servicio específico
docker compose logs -f web
docker compose logs -f db

# Reiniciar todo desde cero si algo quedó en mal estado
docker compose down
docker compose up --build -d

# Ver cuánta memoria/CPU está usando cada contenedor
docker stats
```

Errores comunes:

- **`permission denied` al correr `docker`**: no cerraste sesión
  después del `usermod -aG docker` (Paso 4) — vuelve a conectarte por SSH.
- **`web` se reinicia en bucle**: casi siempre es que `db` no estaba
  listo o el `.env` tiene un valor mal escrito — revisa
  `docker compose logs web` para ver el error real.
- **`could not translate host name "db"`**: ese error es NORMAL si
  corres comandos de Django fuera de Docker (ej. en tu propia
  computadora) — `db` solo existe como nombre dentro de la red de
  Docker Compose. Todo debe correrse con `docker compose exec web ...`
  o `docker compose run web ...`.
- **El servidor se queda sin memoria** (contenedores mueren solos):
  confirma con `free -h` — si tienes solo 2 GB y todo corre a la vez,
  considera subir a 4 GB o cerrar `mailhog`/`debug_toolbar` cuando no
  los uses activamente.

---

## Qué sigue

Cuando tengas dominio: no repitas este proceso desde cero — el
`README.md` (sección "Producción") y `docker-compose.prod.yml` ya
están preparados para ese salto (Gunicorn + Nginx + TLS + backups
automáticos). Antes de darle acceso a la PyME piloto, repasa
`CHECKLIST_SEGURIDAD.md` completo.
