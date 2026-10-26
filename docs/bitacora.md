# Bitácora de avance · QA Copilot

Registro semanal de lo hecho, los problemas encontrados y las decisiones tomadas.
Se completa al cierre de cada semana del plan de trabajo (spec, sección 11).

## Plantilla

```
## SX · dd/mm – dd/mm

**Fecha de registro:** dd/mm/aaaa

### Hecho
-

### Problemas
-

### Decisiones
-

### Próximo
-
```

---

## S3 · 19/10 – 25/10

**Fecha de registro:** 25/10/2026

### Hecho
- Repositorio con la estructura definitiva, `.env.example` documentado, `Makefile` y commits por fase.
- `docker compose up --build` levanta PostgreSQL 16, backend (FastAPI) y frontend (Streamlit) sin pasos manuales: el backend espera la base, aplica las migraciones y carga los datos de ejemplo.
- Modelo de datos completo (las 5 tablas de la sección 8) con una migración inicial de Alembic revisada a mano; `alembic check` queda limpio.
- RF-01 completo: API `GET/POST /historias` y `GET/PUT /historias/{id}` con validaciones, resumen de casos por estado y errores `{"detalle"}`; 3 historias de ejemplo de SauceDemo (inicio de sesión, carrito, checkout) cargadas con un seed idempotente.
- `GET /salud` con estado de la base y configuración del LLM (503 "degradado" si la base no responde).
- Frontend: Panel con métricas, Historias (listado, alta y acceso al detalle), Detalle (ver y editar), y placeholders de Ejecuciones, Catálogo y las secciones de S4/S5. Acerca de muestra `/salud` y el enlace a `/docs`.
- Spike de Playwright (riesgo R-06): Chromium headless corre dentro del contenedor del backend (`make smoke`) y Python lo lanza con `subprocess` y lee el reporte JSON (anticipo del runner de S5).
- 24 pruebas de pytest contra PostgreSQL real (base `qa_copilot_test`), ruff sin errores.
- README, CLAUDE.md, guía de despliegue en Dokploy y 4 diagramas UML en Mermaid (casos de uso, clases, estados del caso, despliegue), validados con mermaid-cli.

### Problemas
- El puerto 8000 estaba ocupado en la máquina de desarrollo por otro proceso: se usó `BACKEND_PORT=8010` en el `.env` local, que para eso es configurable.
- Ruff tomaba la carpeta `alembic/` como un módulo propio y desordenaba los imports: se declaró `alembic` como paquete de terceros en la configuración de isort.
- Ruff marcó `Depends()` como argumento por defecto (B008): se adoptó el estilo `Annotated` (`DbSession`).
- La herramienta de pruebas de Streamlit (AppTest) no encontraba las páginas registradas con un `url_path` distinto del nombre del archivo: se quitaron los `url_path` personalizados (las URLs quedan derivadas del nombre del archivo, por ejemplo `/detalle_historia?id=3`).
- El `TestClient` de FastAPI emite un aviso de deprecación de Starlette que sugiere instalar `httpx2`. No se agregó porque sería una dependencia nueva; queda pendiente de evaluar.

### Decisiones
- La raíz del repositorio es la carpeta del proyecto (`ProyLab60hs/`), no una subcarpeta `qa-copilot/`.
- Versiones verificadas y fijadas: imagen `mcr.microsoft.com/playwright:v1.64.1-noble` + `@playwright/test` 1.64.1, `postgres:16.15-alpine`, `python:3.12.15-slim`, FastAPI 0.162.0, Pydantic 2.14.1, pydantic-settings 2.16.1, SQLAlchemy 2.1.6, Alembic 1.20.1, psycopg 3.3.6, uvicorn 0.54.0, Streamlit 1.66.1, httpx 0.28.1, pytest 9.1.1, ruff 0.17.2.
- El backend corre como usuario no root (`pwuser`): el volumen de evidencias hereda el dueño desde la imagen y no hubo problemas de permisos.
- Las dependencias se declaran en `pyproject.toml` sin empaquetar el código (`packages = []`), para cachear la capa de dependencias. pytest y ruff se instalan en la imagen (extra `dev`) porque las pruebas corren dentro del contenedor.
- **Desvío de la estructura propuesta:** el frontend usa `st.navigation` + `st.Page` (la API actual de Streamlit) en lugar de la carpeta `pages/`, para mostrar los títulos de la spec con tildes ("Panel", "Catálogo"). `Inicio.py` es el punto de entrada y las pantallas están en `frontend/paginas/`. Se agregaron `lib/formato.py` (fechas en hora argentina) y `lib/rutas.py` (rutas de páginas).
- **Desvío menor:** en el Detalle, "Exportar" y "Ejecutar" dicen "Próximamente (S5)" (no S4), para coincidir con el plan de la spec.
- Aislamiento de pruebas con `TRUNCATE ... RESTART IDENTITY` en lugar de una transacción con rollback: dentro de una transacción `now()` no cambia y la prueba de `actualizada_en` no tendría sentido. La base de prueba se migra con Alembic, así que también se prueba la migración.
- `actualizada_en` se asigna en forma explícita al editar, porque `onupdate` no se dispara si los valores no cambian.
- `caso_prueba.generacion_id` es nulo con `ON DELETE SET NULL`: un caso aprobado sobrevive aunque se borre su generación (pensando en RF-11).
- El listado calcula `resumen_casos` (incluye `invalidos`) con una única consulta agrupada, sin N+1.
- Las variables del LLM quedan comentadas en `.env.example`; `Settings` usa `deepseek` / `deepseek-chat` por defecto y `/salud` informa `configurado: false` mientras no haya clave.
- Healthchecks con Python (`urllib`) en lugar de curl, que no está garantizado en las imágenes; el frontend también tiene uno contra `/_stcore/health`.

### Próximo
- Primer despliegue en Dokploy con Cloudflare Tunnel siguiendo `docs/deploy-dokploy.md` (definir los subdominios).
- Comunicar al tutor el cambio a SauceDemo y la elección de Streamlit (spec 2.6).
- S4: catálogo de pasos de SauceDemo (RF-02), integración con DeepSeek y prompt v1 (RF-03), validación (RF-04) y revisión humana (RF-05).
