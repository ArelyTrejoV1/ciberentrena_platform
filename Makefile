.PHONY: dev-up dev-down dev-logs migrate makemigrations shell test lint audit prod-up prod-down prod-logs

# --- Desarrollo ---
dev-up:
	docker compose up --build

dev-down:
	docker compose down

dev-logs:
	docker compose logs -f web

migrate:
	docker compose exec web python manage.py migrate_schemas --shared
	docker compose exec web python manage.py migrate_schemas

makemigrations:
	docker compose exec web python manage.py makemigrations

shell:
	docker compose exec web python manage.py shell

test:
	docker compose exec web pytest

lint:
	docker compose exec web black --check .
	docker compose exec web flake8 .

audit:
	docker compose exec web bandit -r apps config -ll
	docker compose exec web pip-audit

# --- Producción ---
prod-up:
	docker compose -f docker-compose.prod.yml --env-file .env up -d --build

prod-down:
	docker compose -f docker-compose.prod.yml down

prod-logs:
	docker compose -f docker-compose.prod.yml logs -f web
