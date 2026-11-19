# Bitácora de avance · Casewright

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
  - Límite diario de generaciones (RNF-08, `DAILY_GENERATION_LIMIT`, responde 429).
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

---

## S5 · 02/11 – 08/11

**Fecha de registro:** 05/11/2026

### Hecho
- **RF-06 · Exportación:**
  - `services/exportador.py` arma `HU-n.spec.ts` con los casos aprobados: un `test.describe` por historia, un `test("[CP-n] título")` por caso y un `test.step` por cada paso Gherkin. El código sale solo de las plantillas del catálogo.
  - Lo expone `GET /historias/{id}/export`, que responde 409 si no hay casos aprobados.
  - En el Detalle hay un botón «Descargar .spec.ts» y una vista del código.
  - Se cumple CA-06 con una prueba que corre `tsc --noEmit` sobre un archivo exportado.
- **Catálogo v2:**
  - Nuevo paso `presiono el botón de cancelar` (`data-test="cancel"`), el que faltaba en S4.
  - El `contexto` indica a qué pantalla vuelve en cada paso del checkout. Se verificó contra SauceDemo el 05/11.
- **RF-07 · Ejecución:**
  - `POST /historias/{id}/ejecuciones` responde 202 con la ejecución «en curso» y Playwright corre en segundo plano.
  - Usa Chromium headless, 1 worker, sin reintentos, 30 s por test y un tope de 10 minutos por ejecución.
  - Hay una sola ejecución a la vez y lo garantiza la base. Al arrancar, el backend marca como «error» las ejecuciones que un reinicio dejó colgadas.
- **RF-08 · Resultados:**
  - El reporte JSON de Playwright se lee y cada test se asocia a su caso por `[CP-n]`. Se guardan estado, duración, mensaje de error y captura del fallo.
  - El mensaje queda legible: sin colores ANSI, sin el «Call log» interno y con el paso Gherkin que falló.
  - Endpoints: `GET /ejecuciones`, `GET /ejecuciones/{id}` y `GET /evidencias/{id}`.
- **Interfaz:**
  - En el Detalle, botón «Ejecutar pruebas» con el estado de la última ejecución, que se actualiza solo mientras corre (CA-07).
  - Pantalla Ejecuciones con el listado, el detalle por caso, el error, la captura (CA-08) y el log.
  - El Panel muestra las últimas ejecuciones, como adelanto parcial de RF-09.
- 186 pruebas de pytest. Incluyen:
  - una de punta a punta con Playwright real contra SauceDemo, con un caso que pasa y otro que falla y genera su captura;
  - el lector de reportes, probado con un reporte real guardado como muestra (`tests/datos/reporte_playwright.json`).
- La interfaz se recorrió con Playwright: ejecución en curso, uso de la página mientras corre, resumen, error con su captura y Panel.
- Diagrama de secuencia de la exportación y la ejecución, y estados de la ejecución, en [`docs/uml/secuencia-ejecucion.md`](uml/secuencia-ejecucion.md).

### Problemas
- **Separadores de línea Unicode:** al escribir las pruebas de escapado apareció que `str.splitlines()` de Python también corta en U+2028. Un valor con ese carácter partía el literal en dos líneas de TypeScript. Se corrigió en dos partes: las plantillas se dividen solo por `\n` y U+2028 y U+2029 se escapan siempre en los literales.
- **Ubicación del `.spec.ts`:** Playwright no resuelve `@playwright/test` si el archivo está fuera del proyecto. El runner escribe el archivo en `backend/playwright/ejecuciones/<id>/`, que se ignora en Git y en Docker y se borra al terminar. Las salidas (`reporte.json`, capturas y una copia del `.spec.ts`) van al volumen de evidencias.
- **`tsc` y los tipos de Node:** `tsc` fallaba en `playwright.config.ts` porque necesita los tipos de Node. En lugar de agregar `@types/node`, el `tsconfig.json` incluye solo los `*.spec.ts`.
- **Sesión en segundo plano:** FastAPI cierra las dependencias con `yield` antes de correr las tareas en segundo plano, así que la tarea no puede usar la sesión del request. Se agregó la dependencia `FabricaSesiones` para que abra la suya, y en las pruebas se reemplaza por la base de prueba.
- **Tope de tiempo:** cortar solo el proceso de Playwright dejaba vivos sus workers y el navegador. El runner lo lanza en un grupo de procesos propio y, si se agota el tiempo, corta el grupo completo.

### Decisiones
- **Un `test.step` por paso Gherkin:** no lo pide la spec, pero el reporte indica en qué paso falló cada caso y el `.spec.ts` se lee como el escenario.
- **Literales con `json.dumps`:** un literal JSON es un literal de cadena válido en TypeScript. Títulos, pasos y valores entran así. Los comentarios del archivo solo llevan códigos y la versión del catálogo, nunca texto del usuario (RNF-05).
- **Revalidar al exportar:** un caso aprobado se vuelve a validar contra el catálogo actual. Si ya no coincide, la exportación responde 409 con el código del caso y no genera un archivo roto.
- **El archivo que se ejecuta es el que se descarga:** el runner usa el mismo exportador y guarda una copia del `.spec.ts` en las evidencias de cada ejecución.
- **`BackgroundTasks` de FastAPI** en lugar de una cola de tareas (Celery o RQ): con una sola ejecución a la vez y un solo usuario alcanza, y no suma servicios.
- **Una ejecución a la vez con un índice único parcial** (`ux_ejecucion_una_en_curso`) en lugar de un lock en memoria: la base lo garantiza aunque lleguen dos pedidos al mismo tiempo. La API además informa cuál ejecución está corriendo.
- **Actualización en vivo con `st.fragment(run_every=2)`:** solo se redibuja el bloque de la ejecución. Cuando termina, se recarga la página completa para actualizar contadores y botones.
- **Rutas de las capturas:** se guardan relativas a la carpeta de evidencias y se sirven por el id del resultado. La API verifica que la ruta no salga de esa carpeta.
- **Dependencia nueva aprobada:** `typescript` 7.0.2 como devDependency del proyecto Playwright, solo para el `tsc --noEmit` de CA-06.
- Las evidencias no se borran por ahora. Medido en local: unos 25 KB por ejecución sin fallos y unos 110 KB con una captura.

### Próximo
- Probar en producción el flujo completo (exportar, ejecutar y ver una captura) y ensayar la demo del segundo encuentro, que es el flujo de punta a punta.
- S6:
  - Panel completo con casos por estado y resultado de la última ejecución por historia (RF-09).
  - Historial de generaciones (RF-12).
  - Revisión del modo demo (RF-10) y de la regeneración (RF-11), que ya están implementados.
  - Limpieza de evidencias viejas.

---

## S6 · 09/11 – 15/11

**Fecha de registro:** 14/11/2026

### Hecho
- **RF-09 · Panel completo:**
  - `GET /historias` y `GET /historias/{id}` incluyen `ultima_ejecucion` con sus totales y el porcentaje de éxito.
  - El Panel muestra una tabla por historia con los casos por estado y el resultado de su última ejecución, y otra con las últimas 10 ejecuciones con aprobados, fallidos, omitidos y % de éxito (CA-09). Las filas llevan al Detalle o a la ejecución.
- **RF-12 · Historial de generaciones:**
  - `GET /historias/{id}/generaciones` devuelve cada generación, también las fallidas, con fecha, proveedor, modelo, versión del prompt, duración, resultado, error y cantidad de casos válidos e inválidos (CA-12).
  - En el Detalle aparece el desplegable «Historial de generaciones».
- **Revisión de RF-10 y RF-11:** se agregaron pruebas para cada criterio y no aparecieron fallas en el código.
  - CA-11 tal cual lo escribe la spec: con 2 aprobados y 3 pendientes, al regenerar los aprobados se conservan y los pendientes se reemplazan.
  - CA-10: el modo demo genera sin hacer pedidos HTTP.
  - RF-10: las respuestas pregrabadas pasan por la misma validación que las del LLM.
- **Corrección en RF-11:** regenerar ya no borra los resultados de ejecuciones pasadas (ver Problemas).
- Dos migraciones nuevas: `94ce088fe468` (conteo de casos por generación) y `d0d7069ccc61` (`resultado_caso.caso_id` con `ON DELETE SET NULL`). `alembic check` queda limpio y los downgrades se probaron.
- 197 pruebas de pytest, 11 más que en S5.
- La interfaz se recorrió con Playwright: el Panel con datos reales, el historial con generaciones correctas y fallidas en modo demo, y una ejecución real contra SauceDemo seguida de una regeneración.
- Se actualizaron el diagrama de clases, la secuencia de la generación, el README y la checklist de despliegue.
- Con esto quedan implementados todos los requerimientos Must y Should de la spec.
- **Nombre definitivo: Casewright** (15/11).
  - La interfaz muestra el nuevo nombre en todas las pantallas, con el isotipo como favicon y logo de la sidebar y el azul de marca (`#1F37B5`) como color principal.
  - «Acerca de» explica el nombre.
  - El `.spec.ts` exportado dice «Generado por Casewright» y la API se presenta como «Casewright API».
  - La landing del producto vive en `landing/index.html` (PR aparte).

### Problemas
- **Resultados perdidos al regenerar:** si un caso se aprobó, se ejecutó y volvió a pendiente, regenerar lo borraba. El `ON DELETE CASCADE` de `resultado_caso` también borraba sus resultados, y la ejecución quedaba con totales que no coincidían con sus filas y sin la captura. Se cambió a `ON DELETE SET NULL` y la pantalla muestra «Caso reemplazado al regenerar».
- **Conteo de casos por generación:** al principio se calculaba a partir de los casos actuales, pero regenerar borra pendientes y editar revalida, así que el historial cambiaba con el tiempo. Ahora se guarda al generar.
- **Pruebas intermitentes con SauceDemo:** la prueba de punta a punta y el spike de Playwright fallaron en 2 corridas de la suite completa, en semanas distintas del código. Solas pasan siempre y en la corrida con tracebacks no se repitió. Se atribuye a la red o a la latencia hacia SauceDemo. Antes de tomar una falla de esas dos como regresión, se repiten.
- SQLAlchemy 2.1 marca como deprecado `.distinct(columna)` para `DISTINCT ON`. Se usa `postgresql.distinct_on`.
- En la prueba de «sin red» del modo demo no se puede reemplazar `httpx.Client.send`, porque el `TestClient` de FastAPI hereda de `httpx.Client`. Se bloquea el transporte real (`httpx.HTTPTransport`).

### Decisiones
- **La última ejecución viaja con cada historia** en lugar de cruzar historias y ejecuciones en el frontend. Sale en la misma consulta del resumen con un `DISTINCT ON` y no trae el log.
- **El conteo de válidos e inválidos se guarda en `generacion`** (dos columnas nuevas). Las generaciones anteriores quedan en nulo y se muestran vacías, porque recalcularlas daría números falsos.
- **Conservar los resultados con el caso en nulo** en lugar de no borrar los pendientes ejecutados: respeta la regla de RF-11 («los pendientes previos se reemplazan») y no altera el historial de ejecuciones. La copia del `.spec.ts` en las evidencias sigue mostrando qué se ejecutó.
- **Casewright: _Case_ + _-wright_** (sufijo de oficio, como en _playwright_), «el que construye casos de prueba» y un guiño a Playwright.
  - Solo cambia el nombre visible.
  - Los nombres técnicos (paquetes `qa-copilot-*`, imágenes, servicios de compose) y los dominios del despliegue quedan igual, para no tocar la infraestructura antes de la defensa.
  - La spec no se modifica y sigue diciendo QA Copilot; «Acerca de» y el README lo aclaran.
- **Limpieza de evidencias pospuesta:** no la pide la spec y con lo medido en S5 (unos 110 KB por ejecución con captura) el volumen no es un riesgo durante la demo.

### Próximo
- Probar en producción con la checklist de [`docs/deploy-dokploy.md`](deploy-dokploy.md), incluido el flujo de S5 (exportar, ejecutar y ver una captura) que quedó pendiente.
- Congelamiento de funcionalidades el 22/11. Hasta entonces, mejoras de interfaz (el nombre definitivo ya está: Casewright).
- S7: pruebas, corrección de errores, presentaciones y demo pregrabada.

---

## S7 · 16/11 – 22/11 (en curso)

**Fecha de registro:** 19/11/2026

### Hecho
- **Especificación v1.0 cerrada** (PR #15):
  - Pasa a llamarse Casewright y queda en «Versión final: alcance cerrado», con la fila 1.0 en el historial de versiones.
  - Nueva sección 2.7 «Cambios durante el desarrollo», con lo que cambió respecto de la versión 0.1 y el motivo.
  - Se ajustó a lo implementado: OpenRouter con httpx, plantillas del catálogo, formato del caso, catálogo v2, modelo de datos final, subdominios, pendientes resueltos y Claude Code como agente de código.
  - El original es `docs/Casewright_Spec_v1.0.docx` y `docs/spec.md` es su conversión con pandoc.
- **Landing en producción** en `casewright.ordema.app` (PR #16):
  - Es el cuarto servicio del compose: nginx 1.30.7 sirve `landing/index.html`.
  - Es pública: queda fuera de Cloudflare Access.
  - La guía de despliegue, el diagrama de despliegue y el README la incluyen.
- **Corrección en la landing:** la demo dejó de reprogramar un timer cada 16 ms mientras estaba pausada o fuera de pantalla. Medido con Playwright: de 124 llamadas en 2 s a ninguna.
- La documentación del repositorio usa el nombre Casewright (bitácora, guía de despliegue y diagrama de casos de uso).
- **Documentación para Google Drive:** se prepararon en PDF las presentaciones comercial y técnica, el índice de entrega y una copia de cada documento del repositorio.
- **Revisión general:** las 197 pruebas pasan sobre `main` y ruff queda limpio.

### Problemas
- **Docx del spec:** tenía texto dañado en el paso 3 de la sección 4.4 («proyectoproyectoproyecto…»), que no estaba en `docs/spec.md`, y el índice era un campo sin calcular. Se completó con las páginas medidas sobre el documento renderizado.
- **Rama de la landing desactualizada:** la rama del PR #13 había quedado atrás de `main` en los archivos que había que tocar. Se rehízo como PR #16 desde `main`, con el mismo commit de la landing, sin forzar la historia.

### Decisiones
- **Spec v1.0 con una sección de cambios** (2.7) en lugar de reescribir las decisiones originales: queda a la vista qué se planificó y qué se implementó. Dos pendientes de la sección 15 siguen abiertos: la comunicación al tutor y la ficha técnica.
- **La landing es un contenedor propio dentro del mismo compose:**
  - Streamlit no sirve HTML arbitrario en la raíz, así que no se integra al frontend.
  - Tampoco se separa en otra aplicación de Dokploy: un único despliegue publica todo.
  - Es pública porque no expone datos ni la API.
- **Drive como repositorio oficial de la documentación:** ahí se publican los PDF; el repositorio conserva los `.md` como fuente y cada PDF enlaza a su original en GitHub.

### Próximo
- Demo pregrabada del flujo completo.
- Congelamiento de funcionalidades el 22/11 y tercer encuentro.
- S8: verificación final del despliegue y de SauceDemo, y ensayo de la defensa.
