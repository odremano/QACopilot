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

---

## S4 · 26/10 – 01/11

**Fecha de registro:** 05/11/2026

### Hecho
- **Despliegue en Dokploy** con Cloudflare Tunnel en `qa.ordema.app` (interfaz) y `qa-api.ordema.app` (API), los dos protegidos con **Cloudflare Access**, que estaba previsto para S6.
- **RF-02:** catálogo de 28 pasos de SauceDemo en `backend/catalogo/saucedemo.yaml`, con un paso por acción y su plantilla de Playwright. Cubre los grupos de inicio de sesión, inventario, carrito, checkout y general, con selectores `data-test` verificados contra la aplicación el 04/11. El cargador valida el archivo con Pydantic: identificadores y patrones únicos, un único parámetro `"{texto}"` entre comillas que también debe estar en la plantilla, y presencia de los grupos obligatorios. Si el archivo es inválido, el backend no inicia (CA-02). La pantalla Catálogo lo muestra en modo de solo lectura.
- **RF-04:** validador en `services/validador.py`. Revisa el JSON y el esquema con Pydantic y la sintaxis Gherkin con `gherkin-official`. Exige un único Escenario sin Característica, Esquema ni tablas, y compara cada paso con el catálogo sin distinguir mayúsculas ni cantidad de espacios. Los errores se informan en español con el número y el texto del paso.
- **RF-03:**
  - Generación con IA mediante OpenRouter y el modelo `deepseek/deepseek-v4.1-flash-1017`. Usa el prompt de sistema versionado `prompts/v1.md` (Anexo A), que incluye el catálogo agrupado por pantalla, los datos reales de SauceDemo y el ejemplo del Anexo B.
  - Pide salida JSON y reintenta hasta 2 veces si la respuesta no respeta el formato o las reglas: de 3 a 8 casos, con al menos un positivo y un negativo.
  - Cada generación queda registrada en `generacion` con los intentos crudos, la duración y el error, también las fallidas.
  - Una generación real tarda entre 6 y 12 s y produce unos 7 casos válidos por historia.
- **Adelantos de S6:**
  - Límite diario de generaciones (RNF-08, `LLM_DAILY_LIMIT`, responde 429).
  - Modo demo (`LLM_PROVIDER=demo`) con respuestas pregrabadas de las tres historias de ejemplo en `backend/demo/`.
  - Regeneración que reemplaza los casos pendientes y conserva los aprobados y descartados (base de RF-11).
- **RF-05:**
  - Revisión humana desde la tarjeta de cada caso: aprobar (solo los válidos), descartar, volver a pendiente y editar.
  - La edición solo se permite en estado pendiente y siempre revalida el caso.
  - Las transiciones inválidas responden 409 con el motivo.
  - Se cumplen los 4 escenarios de CA-05.
- `GET /` redirige a `/docs`.
- 146 pruebas de pytest, incluidas las del catálogo, el validador, el proveedor LLM con transporte simulado, la generación con un proveedor falso y la máquina de estados. Ruff y `alembic check` quedan limpios.
- La interfaz se verificó con Playwright: generación, edición de un caso inválido, aprobación, descarte y vuelta a pendiente.
- Diagrama de secuencia de la generación y la revisión en [`docs/uml/secuencia-generacion.md`](uml/secuencia-generacion.md).

### Problemas
- **S4 cerró 4 días tarde** (el 05/11 en lugar del 01/11), lo que achica el margen de S5 antes del segundo encuentro. Lo compensa en parte haber adelantado Cloudflare Access, el límite diario, el modo demo y la regeneración, que estaban previstos para S6.
- El parser de `gherkin-official` no marca como error las líneas sin palabra clave ni las palabras clave en inglés (`Scenario:`): las toma como descripción en silencio. Se agregó una verificación propia de texto libre con su mensaje.
- Primero el modelo usó valores inventados, como mensajes de error y totales que no existen en SauceDemo. Se sumó al catálogo un bloque `contexto` con datos verificados en el código de la aplicación el 05/11 (usuarios, mensajes, productos, precios, órdenes, títulos y el impuesto del 8 %), y el prompt le indica al modelo usar solo esos valores.
- El modelo de DeepSeek razona por defecto y eso consumía tokens y tiempo. Con OpenRouter se envía `reasoning: {"exclude": true}` y `max_tokens` amplio para que el JSON no quede cortado.
- **Falta un paso en el catálogo:** no hay paso para el botón «Cancel» del checkout, así que el modelo propuso un caso de «cancelar» con el paso de «seguir comprando». Es válido contra el catálogo pero no prueba lo que dice. Se dejó en la respuesta demo de Checkout como ejemplo de por qué hace falta la revisión humana, y el paso se agrega en S5.
- `ruff format` dentro del contenedor no modifica los archivos del host, porque no hay volúmenes de código montados. Se formatea desde el host con la misma versión de ruff.
- La interfaz de Cloudflare Zero Trust cambió de nombres respecto de las guías conocidas: se siguió la documentación oficial actual.

### Decisiones
- **OpenRouter en lugar de la API directa de DeepSeek:** da acceso al mismo modelo con una sola clave y un límite de crédito configurable. La API es compatible con OpenAI, así que volver a DeepSeek directo solo requiere cambiar `LLM_PROVIDER`, `LLM_BASE_URL` y `LLM_MODEL`.
- **httpx en lugar del SDK de OpenAI:** es una sola llamada `POST /chat/completions` y httpx ya era dependencia del proyecto, así que no se agregó un paquete nuevo. Pasó de las dependencias de desarrollo a las principales.
- **Corrección del formato de salida:** en la fase de RF-04 el esquema esperaba un campo `gherkin` con texto libre, pero el Anexo B define `pasos` como lista. Se ajustó al Anexo B. El modelo devuelve `{titulo, tipo, pasos}` y el backend arma `Escenario: <título>` con un paso por línea, así que el LLM no escribe la estructura Gherkin.
- **Un caso es un único Escenario,** sin Característica, Esquema ni tablas. Simplifica la validación y la exportación, y alcanza para los flujos de SauceDemo.
- La coincidencia con el catálogo no distingue mayúsculas ni cantidad de espacios. El valor del parámetro se conserva tal cual porque el exportador lo usará en S5.
- El **contexto del SUT** forma parte del catálogo (`contexto` en el YAML): son datos de la aplicación objetivo y se versionan junto con sus pasos.
- Los errores del proveedor (clave, crédito, límite de solicitudes, timeout) no se reintentan, porque repetirlos no los resuelve. Solo se reintentan las respuestas mal formadas.
- El límite diario cuenta todas las generaciones desde las 00:00 en hora argentina (UTC-3, sin horario de verano). El valor 0 significa sin límite.
- El modo demo elige la respuesta por el título de la historia. Las respuestas son salidas reales del modelo, guardadas sin retocar.
- Transiciones de estado declaradas en una tabla única (`TRANSICIONES` en `services/casos.py`), con un 409 y su mensaje por cada transición inválida.
- Al editar un caso, si queda válido, el título se toma de su línea «Escenario:». Si queda inválido, se conserva el título anterior.
- Cloudflare Access se activó en S4 para no dejar expuesta la API con una clave de LLM con crédito.

### Próximo
- S5:
  - Generador TypeScript (RF-06): `.spec.ts` desde las plantillas del catálogo, con los parámetros escapados como literales.
  - Runner de Playwright (RF-07).
  - Resultados con capturas (RF-08).
- Agregar al catálogo el paso del botón «Cancel» del checkout.
- Segundo encuentro: mostrar el flujo de punta a punta, desde la historia hasta la ejecución.
