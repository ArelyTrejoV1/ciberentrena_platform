# Imagen base para web, worker y beat (mismo código, distinto comando de arranque)
FROM python:3.12-slim AS base

# No correr como root dentro del contenedor
RUN groupadd -r appuser && useradd -r -g appuser appuser

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ARG REQUIREMENTS_FILE=requirements/prod.txt
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r ${REQUIREMENTS_FILE}

COPY . .

RUN mkdir -p /app/staticfiles /app/mediafiles && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

ENTRYPOINT ["docker/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--config", "docker/gunicorn_conf.py"]
