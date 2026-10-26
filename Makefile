# Atajos de desarrollo. Todos operan vía docker compose.
COMPOSE := docker compose

.PHONY: up down logs test lint format migrate revision psql smoke

up: ## Construye y levanta los servicios en segundo plano
	$(COMPOSE) up --build -d

down: ## Detiene y elimina los contenedores (conserva los volúmenes)
	$(COMPOSE) down

logs: ## Muestra los logs de todos los servicios
	$(COMPOSE) logs -f --tail=100

test: ## Corre las pruebas del backend
	$(COMPOSE) exec backend pytest

lint: ## Lint y chequeo de formato (backend y frontend)
	$(COMPOSE) exec backend ruff check .
	$(COMPOSE) exec backend ruff format --check .
	$(COMPOSE) exec frontend ruff check .
	$(COMPOSE) exec frontend ruff format --check .

format: ## Aplica el formato y las correcciones automáticas de ruff
	$(COMPOSE) exec backend ruff check --fix .
	$(COMPOSE) exec backend ruff format .
	$(COMPOSE) exec frontend ruff check --fix .
	$(COMPOSE) exec frontend ruff format .

migrate: ## Aplica las migraciones y verifica que no haya cambios pendientes
	$(COMPOSE) exec backend alembic upgrade head
	$(COMPOSE) exec backend alembic check

revision: ## Genera una migración: make revision m="descripcion"
	$(COMPOSE) exec backend alembic revision --autogenerate -m "$(m)"

psql: ## Abre psql dentro del contenedor de la base
	$(COMPOSE) exec db sh -c 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

smoke: ## Spike de Playwright dentro del contenedor del backend
	$(COMPOSE) exec backend sh -c "cd playwright && npx playwright test smoke"
	$(COMPOSE) exec backend node -e "const r = require('/data/evidencias/smoke/reporte.json'); console.log('Reporte JSON generado:', JSON.stringify(r.stats))"
