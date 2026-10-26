# CLAUDE.md · QA Copilot

App web full stack: el analista QA carga historias de usuario, un LLM propone casos Gherkin en español validados contra un catálogo de pasos, la persona los revisa y aprueba, se exportan a un `.spec.ts` de Playwright generado por plantillas y se ejecutan contra SauceDemo. **La IA propone, el sistema valida y la persona decide.** Proyecto final UB, un solo desarrollador, defensa el 26/11/2026: priorizar lo simple que funcione de punta a punta.

## Fuentes de verdad

- Especificación: `docs/spec.md` (alcance MoSCoW, RF/CA, modelo de datos, API, pantallas). **No modificarla.**
- Avance y decisiones: `docs/bitacora.md` (completar al cerrar cada semana).
- Diagramas: `docs/uml/` (Mermaid). Despliegue: `docs/deploy-dokploy.md`.

## Stack

- Backend (`backend/`): Python 3.12, FastAPI, Pydantic v2, pydantic-settings, SQLAlchemy 2 **sincrónico** (`Mapped`/`mapped_column`), Alembic, psycopg 3, uvicorn. Imagen base: Playwright oficial + venv en `/opt/venv`, usuario `pwuser`.
- Frontend (`frontend/`): Streamlit con `st.navigation` (`Inicio.py` → `paginas/`), httpx.
- PostgreSQL 16. Playwright Test + TypeScript en `backend/playwright/` (versión de `@playwright/test` = tag de la imagen).
- Calidad: pytest (contra PostgreSQL real, base `<db>_test`), ruff.

## Convenciones

- Idioma: UI, mensajes, docs y commits en español. Dominio en español como en la spec (`historia_usuario`, `CasoPrueba`, `/historias`, `/salud`); lo técnico en inglés snake_case (`get_db`, `settings`).
- Estados: `String` + `CheckConstraint`, valores definidos una sola vez en `app/models/estados.py` (StrEnum). Nada de ENUM nativo.
- Códigos visibles `HU-n` / `CP-n`: se calculan desde el `id`, no se guardan.
- Errores de la API: `{"detalle": "mensaje en español"}` (`app/errors.py`: `ErrorNegocio`, `NoEncontrado`). Los 422 de Pydantic quedan estándar y el frontend los traduce.
- Routers solo traducen HTTP ↔ servicio; la lógica va en `app/services/`.
- Frontend: **solo** `frontend/lib/api.py` habla con el backend (excepción `ErrorApi`). Ninguna página usa httpx ni accede a la base (RF-09).
- **El LLM nunca genera código ejecutable**: solo pasos del catálogo; el TypeScript sale de plantillas y los parámetros se escapan como literales (RNF-05).
- Configuración solo por variables de entorno (`.env.example` documentado, `.env` nunca se versiona).

## Comandos

```bash
cp .env.example .env && docker compose up --build   # levantar todo
make up | down | logs
make test        # pytest dentro del backend
make lint        # ruff check + format --check (backend y frontend)
make format
make migrate     # alembic upgrade head + alembic check
make revision m="descripcion"
make smoke       # Playwright smoke dentro del backend
make psql
```

Tras cambiar código: `docker compose up --build -d <servicio>` (no hay volúmenes de código montados).

## Reglas de trabajo

- Planificar antes de codear y esperar el OK; trabajar por fases con verificación y un commit por fase (Conventional Commits en español).
- No inventar versiones: verificarlas (`pip index versions`, `npm view`, tags de imágenes) y fijarlas exactas.
- No agregar dependencias sin preguntar. No tocar `docs/spec.md`.
- Si algo falla dos veces con el mismo enfoque, frenar y explicar alternativas.
- Migraciones: autogenerate + revisión manual; `alembic check` debe quedar limpio.

## Fuera de alcance (spec 3.3)

Autenticación/roles, historial de versiones de casos, más de un SUT o configurarlo desde la UI, editar el catálogo desde la UI, código libre del LLM, ejecución multi-navegador/paralela/programada/CI, video, integraciones (Jira, TestRail), fine-tuning, app móvil, datos reales al LLM. Tampoco hay borrado de historias.
