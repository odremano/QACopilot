Universidad de Belgrano

Tecnicatura en Programación de Computadoras (560) · Prácticas de Laboratorio

**Casewright**

Especificación de requerimientos y alcance del MVP

*Generación asistida por IA de casos de prueba Gherkin y scripts de Playwright a partir de historias de usuario*

| **Autor**                 | Jesús Alejandro Odreman Silva       |
|---------------------------|-------------------------------------|
| **Docente tutor**         | Mg. Ing. Guillermo Ramiro Maquieira |
| **Versión del documento** | 1.0                                 |
| **Fecha**                 | 19/11/2026                          |
| **Estado**                | Versión final: alcance cerrado      |
| **Fecha de defensa**      | 26/11/2026                          |

# Historial de versiones

Cada cambio del documento se registra en esta tabla. Se incrementa la versión menor (0.x) ante ajustes y la versión mayor (1.0) cuando el alcance queda congelado para el desarrollo.

| **Versión** | **Fecha**  | **Autor**     | **Descripción del cambio**                                                                                                                                                                                                                                                                                                                                                                                                                       |
|-------------|------------|---------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 0.1         | 18/10/2026 | Jesús Odreman | Borrador inicial: alcance del MVP, decisiones técnicas, requerimientos funcionales y no funcionales, criterios de aceptación, modelo de datos, interfaces, riesgos y plan de trabajo.                                                                                                                                                                                                                                                            |
| 1.0         | 19/11/2026 | Jesús Odreman | Versión final para la entrega. El producto pasa a llamarse Casewright (nombre de trabajo: QA Copilot). El documento se ajusta a lo implementado: acceso al LLM por OpenRouter con httpx, código generado con las plantillas del catálogo, formato del caso, catálogo v2, modelo de datos final, subdominios del despliegue y uso de IA en el desarrollo. Se agrega la sección 2.7 con los cambios durante el desarrollo y se completa el índice. |
|             |            |               |                                                                                                                                                                                                                                                                                                                                                                                                                                                  |

# Índice

- [Historial de versiones](#historial-de-versiones)
- [1. Introducción](#1-introducción)
  - [1.1 Propósito](#11-propósito)
  - [1.2 Alcance del documento](#12-alcance-del-documento)
  - [1.3 Glosario](#13-glosario)
  - [1.4 Referencias](#14-referencias)
- [2. Descripción general](#2-descripción-general)
  - [2.1 Contexto y problema](#21-contexto-y-problema)
  - [2.2 Objetivo del MVP](#22-objetivo-del-mvp)
  - [2.3 Actores](#23-actores)
  - [2.4 Supuestos](#24-supuestos)
  - [2.5 Restricciones](#25-restricciones)
  - [2.6 Cambios respecto de la propuesta aprobada](#26-cambios-respecto-de-la-propuesta-aprobada)
  - [2.7 Cambios durante el desarrollo](#27-cambios-durante-el-desarrollo)
- [3. Alcance](#3-alcance)
  - [3.1 Incluido en el MVP (Must)](#31-incluido-en-el-mvp-must)
  - [3.2 Deseable (Should) y opcional (Could)](#32-deseable-should-y-opcional-could)
  - [3.3 Fuera de alcance (Won't)](#33-fuera-de-alcance-wont)
- [4. Arquitectura y decisiones técnicas](#4-arquitectura-y-decisiones-técnicas)
  - [4.1 Vista general](#41-vista-general)
  - [4.2 Stack tecnológico](#42-stack-tecnológico)
  - [4.3 Decisiones técnicas](#43-decisiones-técnicas)
  - [4.4 Flujo principal de punta a punta](#44-flujo-principal-de-punta-a-punta)
- [5. Requerimientos funcionales](#5-requerimientos-funcionales)
- [6. Requerimientos no funcionales](#6-requerimientos-no-funcionales)
- [7. Criterios de aceptación](#7-criterios-de-aceptación)
- [8. Modelo de datos](#8-modelo-de-datos)
  - [8.1 Estados del caso de prueba](#81-estados-del-caso-de-prueba)
- [9. Interfaces](#9-interfaces)
  - [9.1 API REST](#91-api-rest)
  - [9.2 Pantallas](#92-pantallas)
  - [9.3 Integración con el LLM](#93-integración-con-el-llm)
  - [9.4 Integración con Playwright](#94-integración-con-playwright)
- [10. Riesgos y mitigaciones](#10-riesgos-y-mitigaciones)
- [11. Plan de trabajo](#11-plan-de-trabajo)
- [12. Entregables académicos](#12-entregables-académicos)
- [13. Uso de inteligencia artificial en el desarrollo](#13-uso-de-inteligencia-artificial-en-el-desarrollo)
- [14. Matriz de trazabilidad](#14-matriz-de-trazabilidad)
- [15. Pendientes y preguntas abiertas](#15-pendientes-y-preguntas-abiertas)
- [Anexo A · Estructura del prompt (v1)](#anexo-a--estructura-del-prompt-v1)
- [Anexo B · Ejemplo de salida del LLM](#anexo-b--ejemplo-de-salida-del-llm)
- [Anexo C · Del Gherkin al script](#anexo-c--del-gherkin-al-script)
  - [C.1 Caso aprobado (CP-12 de la historia HU-1)](#c1-caso-aprobado-cp-12-de-la-historia-hu-1)
  - [C.2 Script generado (HU-1.spec.ts)](#c2-script-generado-hu-1spects)
- [Anexo D · Ejemplo del catálogo de pasos](#anexo-d--ejemplo-del-catálogo-de-pasos)

# 1. Introducción

## 1.1 Propósito

Este documento define el alcance, los requerimientos, los criterios de aceptación y el plan del producto mínimo viable (MVP) de Casewright, proyecto final de Prácticas de Laboratorio. Es la referencia para el desarrollo, para los encuentros de seguimiento con el tutor y para la defensa. También fue la especificación de referencia para el desarrollo asistido por IA (sección 13).

## 1.2 Alcance del documento

Cubre el producto de software y los entregables académicos exigidos por los lineamientos de la materia. No reemplaza a la ficha técnica (Word) ni a las presentaciones, sino que las alimenta.

## 1.3 Glosario

| **Término**           | **Definición**                                                                                                                                                          |
|-----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **HU**                | Historia de usuario: requisito expresado en lenguaje natural (Como… quiero… para…), con sus criterios de aceptación.                                                    |
| **CP**                | Caso de prueba: un escenario Gherkin generado a partir de una HU.                                                                                                       |
| **LLM**               | Modelo de lenguaje de gran escala, usado para proponer casos de prueba.                                                                                                 |
| **Gherkin**           | Lenguaje estructurado (Dado / Cuando / Entonces) para describir comportamiento. Se usa en español con la directiva \# language: es.                                     |
| **Playwright**        | Herramienta de automatización de pruebas web. En este proyecto se usa Playwright Test con TypeScript.                                                                   |
| **SUT**               | Sistema bajo prueba (System Under Test). En el MVP: SauceDemo (Swag Labs).                                                                                              |
| **Catálogo de pasos** | Lista cerrada de pasos Gherkin permitidos para el SUT, cada uno asociado a una plantilla de código Playwright con sus selectores.                                       |
| **Modo demo**         | Configuración en la que la generación usa respuestas pregrabadas en lugar de llamar al proveedor del LLM.                                                               |
| **MoSCoW**            | Priorización: Must (imprescindible), Should (deseable), Could (opcional), Won't (fuera de alcance).                                                                     |
| **MVP**               | Producto mínimo viable: la versión más chica del producto que cumple el flujo completo de punta a punta.                                                                |
| **Casewright**        | Nombre del producto: Case (caso de prueba) + -wright (sufijo de oficio, como en playwright), «el que construye casos de prueba». Nombre de trabajo inicial: QA Copilot. |
| **OpenRouter**        | Servicio que da acceso a modelos de distintos proveedores con una API compatible con OpenAI y una sola clave. Se usa para acceder al modelo de DeepSeek.                |

## 1.4 Referencias

- Propuesta de Prácticas de Laboratorio “QA Copilot” (aprobada por el tutor), nombre de trabajo de Casewright.

- Maquieira, G. R. Prácticas de Laboratorio: Primer Encuentro y Lineamientos y Rúbrica (material de la cátedra).

- Referencias sugeridas por el tutor: TestFirst (testfirst.com) y Streamlit (streamlit.io).

- Cucumber. Gherkin Reference. https://cucumber.io/docs/gherkin/reference/

- Playwright. Documentación oficial. https://playwright.dev/docs/intro

- DeepSeek. JSON Output. https://api-docs.deepseek.com/guides/json_mode

- OpenRouter. Documentación oficial. https://openrouter.ai/docs

- Sauce Labs. SauceDemo (Swag Labs). https://www.saucedemo.com

- Wang, J. et al. Software Testing with Large Language Models: Survey, Landscape, and Vision. IEEE TSE, 2024.

# 2. Descripción general

## 2.1 Contexto y problema

Diseñar casos de prueba a partir de requisitos escritos en lenguaje natural es una tarea manual, repetitiva y propensa a omisiones, sobre todo en escenarios negativos y de valores límite. Automatizarlos luego exige tiempo adicional y conocimiento de herramientas como Playwright. Los LLM pueden asistir en esta tarea, pero su salida no es determinista y puede contener errores.

## 2.2 Objetivo del MVP

Entregar una aplicación web full stack que permita, para una aplicación objetivo de práctica: cargar una historia de usuario, generar con IA casos de prueba Gherkin en español, validarlos contra un catálogo de pasos, revisarlos y aprobarlos, exportarlos a un script de Playwright en TypeScript, ejecutarlos y ver los resultados con evidencias en un panel.

Principio rector: **la IA propone, el sistema valida y la persona decide.** El LLM nunca escribe código ejecutable.

## 2.3 Actores

| **Actor**            | **Tipo**              | **Descripción**                                                                                                                                                                                    |
|----------------------|-----------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Analista QA**      | Usuario (único)       | Carga historias, genera, revisa y aprueba casos, exporta y ejecuta pruebas, consulta resultados.                                                                                                   |
| **Proveedor de LLM** | Sistema externo       | API compatible con OpenAI que devuelve casos en JSON. Por defecto, OpenRouter con el modelo deepseek/deepseek-v4.1-flash-1017; DeepSeek directo u Ollama local se usan cambiando la configuración. |
| **SauceDemo**        | Sistema externo (SUT) | Sitio público de práctica contra el que se ejecutan las pruebas.                                                                                                                                   |
| **Administrador**    | Operación             | Despliega y configura el sistema (variables de entorno, proveedor de LLM, límites).                                                                                                                |

## 2.4 Supuestos

- SauceDemo permanece disponible y con selectores estables durante el desarrollo y la defensa.

- Se dispone de una clave de OpenRouter con crédito suficiente para el desarrollo y la demo (consumo esperado bajo), acotada con un límite de crédito.

- El servidor propio (Proxmox + Dokploy) y el túnel de Cloudflare están operativos.

- Las historias de usuario se refieren a funcionalidades del SUT cubiertas por el catálogo de pasos.

## 2.5 Restricciones

- **Tiempo:** defensa el 26/11/2026.

- **Equipo:** un único desarrollador.

- **Datos:** solo historias y datos de ejemplo; no se envían datos reales o confidenciales al LLM.

- **Costo:** proveedor de LLM económico o local; infraestructura propia.

- **SUT de terceros:** uso responsable (ejecución manual, sin concurrencia, sin carga).

## 2.6 Cambios respecto de la propuesta aprobada

Los siguientes ajustes concretan o modifican lo indicado en la propuesta. El cambio de aplicación objetivo contradice una exclusión explícita de la propuesta, por lo que conviene comunicarlo al tutor antes del segundo encuentro.

| **Tema**                | **Propuesta aprobada**                                                                                       | **Este documento**                                                                               | **Motivo**                                                                                                                                 |
|-------------------------|--------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------|
| **Aplicación objetivo** | Aplicación web de ejemplo incluida en el proyecto. “Ejecución contra sistemas de terceros” fuera de alcance. | SauceDemo, sitio público diseñado para practicar testing.                                        | Ahorra el desarrollo de una app propia; el sitio existe para este fin. **A comunicar al tutor.**                                           |
| **Interfaz web**        | Interfaz web (sin definir).                                                                                  | Streamlit (Python).                                                                              | Herramienta sugerida por el tutor; menor tiempo de desarrollo.                                                                             |
| **Base de datos**       | Base relacional (sin definir).                                                                               | PostgreSQL.                                                                                      | Robusta, estándar y soportada en el servidor propio.                                                                                       |
| **Proveedor LLM**       | API de un proveedor (sin definir).                                                                           | DeepSeek (a través de OpenRouter) por defecto; DeepSeek directo u Ollama local como alternativa. | Bajo costo y API compatible con OpenAI. OpenRouter permite fijar un límite de crédito a la clave.                                          |
| **Scripts**             | Playwright.                                                                                                  | Playwright Test en TypeScript.                                                                   | Es el lenguaje más difundido en el ecosistema Playwright.                                                                                  |
| **Nombre**              | QA Copilot.                                                                                                  | Casewright.                                                                                      | Nombre comercial definitivo, elegido el 15/11/2026. Los identificadores técnicos del repositorio y los dominios del despliegue no cambian. |

## 2.7 Cambios durante el desarrollo

Durante el desarrollo se tomaron decisiones que concretan o modifican lo previsto en la versión 0.1 de este documento. Ninguna cambia el alcance Must ni el principio rector. El detalle de cada una está en la bitácora de avance (docs/bitacora.md).

| **Tema**                              | **Versión 0.1**                              | **Versión 1.0 (implementado)**                                                                                                             | **Motivo**                                                                                                                                        |
|---------------------------------------|----------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|
| **Nombre del producto**               | QA Copilot.                                  | Casewright.                                                                                                                                | Nombre comercial definitivo (15/11/2026): Case + -wright, «el que construye casos de prueba», con un guiño a Playwright.                          |
| **Acceso al LLM**                     | API de DeepSeek con el SDK de OpenAI.        | OpenRouter con el modelo deepseek/deepseek-v4.1-flash-1017, llamado con httpx.                                                             | Una sola clave con límite de crédito. Es una única llamada HTTP y httpx ya era dependencia del proyecto.                                          |
| **Generación de código**              | Plantillas Jinja2.                           | Plantillas del catálogo; los parámetros se insertan como literales escapados con json.dumps.                                               | Cada paso tiene una plantilla de pocas líneas y no hace falta un motor de plantillas. RNF-05 se mantiene.                                         |
| **Formato del caso**                  | Característica con un Escenario (Anexo C.1). | Un único Escenario por caso, sin Característica, Esquema ni tablas. El LLM devuelve solo la lista de pasos y el sistema arma el Escenario. | Simplifica la validación y la exportación, y alcanza para los flujos de SauceDemo.                                                                |
| **Catálogo de pasos**                 | Extracto ilustrativo (Anexo D).              | Versión 2 con 29 pasos y un bloque «contexto» con usuarios, mensajes, productos y títulos verificados en SauceDemo.                        | Sin esos datos, el modelo inventaba mensajes y totales que la aplicación no muestra.                                                              |
| **Script exportado**                  | Un test por caso.                            | Un test por caso y un test.step por cada paso Gherkin.                                                                                     | El reporte indica en qué paso falló cada caso y el script se lee como el escenario.                                                               |
| **Modelo de datos**                   | Sección 8 de la versión 0.1.                 | Conteo de casos válidos e inválidos en generacion; resultado_caso.caso_id admite nulo; índice único parcial para la ejecución en curso.    | Historial de generaciones estable (RF-12), regenerar no borra resultados pasados (RF-11) y la base garantiza una sola ejecución a la vez (RF-07). |
| **Cloudflare Access y límite diario** | Previstos para S6.                           | Activos desde S4.                                                                                                                          | No dejar expuesta la API con una clave del LLM con crédito.                                                                                       |
| **Requerimientos Could**              | RF-13 a RF-16, opcionales.                   | No implementados.                                                                                                                          | Se priorizó completar los Must y los Should antes del congelamiento del 22/11.                                                                    |

# 3. Alcance

Se aplica priorización MoSCoW. El MVP queda definido por los requerimientos **Must**; los **Should** se implementan si el plan se cumple; los **Could** solo si sobra tiempo tras el congelamiento.

## 3.1 Incluido en el MVP (Must)

- Gestión de historias de usuario (alta, edición, listado y detalle), con historias de ejemplo precargadas.

- Catálogo de pasos y selectores de SauceDemo (inicio de sesión, inventario, carrito y checkout), versionado en el repositorio.

- Generación de casos Gherkin en español (positivos, negativos y de valores límite) mediante un LLM con salida JSON.

- Validación automática de la salida: esquema JSON, sintaxis Gherkin y pertenencia de cada paso al catálogo.

- Revisión humana: editar, aprobar o descartar cada caso.

- Exportación de los casos aprobados a un archivo .spec.ts de Playwright, generado de forma determinista por plantillas.

- Ejecución en segundo plano contra SauceDemo (Chromium headless), con registro de resultados y captura de pantalla en los fallos.

- Panel con historial de historias, casos, ejecuciones y reporte de resultados.

- Despliegue con Docker Compose en Dokploy bajo subdominios de ordema.app (qa.ordema.app para la interfaz y qa-api.ordema.app para la API).

## 3.2 Deseable (Should) y opcional (Could)

| **Prioridad** | **Funcionalidad**                                                                    |
|---------------|--------------------------------------------------------------------------------------|
| **Should**    | Modo demo con respuestas pregrabadas del LLM                                         |
| **Should**    | Regenerar los casos de una historia.                                                 |
| **Should**    | Historial de generaciones visible (modelo, versión del prompt, duración, resultado). |
| **Should**    | Pruebas unitarias propias del validador y del generador de código.                   |
| **Could**     | Métricas de calidad de la IA (tasa de aprobación, casos descartados e inválidos).    |
| **Could**     | Trace de Playwright descargable.                                                     |
| **Could**     | Exportación .zip con el proyecto Playwright completo.                                |
| **Could**     | Regenerar un caso puntual.                                                           |

## 3.3 Fuera de alcance (Won't)

- Autenticación multiusuario, roles y permisos dentro de la aplicación.

- Historial de versiones de los casos de prueba.

- Más de una aplicación objetivo, o configuración de aplicaciones objetivo desde la interfaz.

- Edición del catálogo de pasos desde la interfaz (se edita en el repositorio).

- Generación de código libre por parte del LLM.

- Ejecución en varios navegadores, en paralelo, programada o integrada a CI.

- Grabación de video de las ejecuciones.

- Integraciones con Jira, TestRail u otras herramientas de gestión.

- Entrenamiento o ajuste fino de modelos.

- Aplicación móvil.

- Envío de datos reales o confidenciales al proveedor del LLM.

# 4. Arquitectura y decisiones técnicas

## 4.1 Vista general

El sistema se compone de tres contenedores y dos servicios externos. El frontend no accede a la base de datos: toda la lógica vive en la API, lo que mantiene la separación full stack y permite reemplazar la interfaz en el futuro sin tocar el backend.

> \[Navegador\]
>
> \| HTTPS (Cloudflare Tunnel + Access)
>
> v
>
> +-------------+ REST/JSON +-------------------------------+
>
> \| Frontend \| --------------\> \| Backend (FastAPI) \|
>
> \| Streamlit \| \| - API REST + OpenAPI (/docs) \|
>
> +-------------+ \| - Servicio de generación IA \|
>
> \| - Validador Gherkin/catálogo \|
>
> \| - Generador de código (TS) \|
>
> \| - Runner Playwright (Node) \|
>
> +---------------+---------------+
>
> \| \| \|
>
> SQL \| HTTPS \| HTTPS \|
>
> v v v
>
> \[PostgreSQL\] \[API LLM: \[SauceDemo\]
>
> OpenRouter\]

## 4.2 Stack tecnológico

| **Capa**                 | **Tecnología**                                                                                                                  | **Uso**                                                                   |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| **Frontend**             | Streamlit (Python)                                                                                                              | Pantallas de historias, revisión, ejecuciones y panel.                    |
| **Backend**              | Python 3.12, FastAPI, Pydantic, SQLAlchemy 2, Alembic                                                                           | API REST, validación, persistencia y migraciones.                         |
| **Base de datos**        | PostgreSQL 16                                                                                                                   | Persistencia de historias, generaciones, casos, ejecuciones y resultados. |
| **IA**                   | httpx contra la API de OpenRouter (compatible con OpenAI) con un modelo de DeepSeek; DeepSeek directo u Ollama como alternativa | Generación de casos con salida JSON.                                      |
| **Gherkin**              | Parser oficial de Cucumber (paquete gherkin-official)                                                                           | Validación sintáctica de los escenarios en español.                       |
| **Generación de código** | Plantillas del catálogo de pasos con literales escapados (json.dumps)                                                           | Traducción determinista de pasos a TypeScript.                            |
| **Automatización**       | Playwright Test 1.64.1 (TypeScript) sobre la imagen oficial de Playwright, Chromium                                             | Ejecución de los scripts y capturas.                                      |
| **Infraestructura**      | Docker, Docker Compose, Dokploy, Cloudflare Tunnel y Access                                                                     | Despliegue en el servidor propio con HTTPS.                               |
| **Calidad**              | pytest (197 pruebas contra PostgreSQL real), ruff                                                                               | Pruebas unitarias propias y estilo de código.                             |
| **Repositorio**          | GitHub                                                                                                                          | Código fuente, README y catálogo de pasos.                                |

## 4.3 Decisiones técnicas

### DEC-01 · Frontend con Streamlit

Se evaluaron tres opciones:

| **Opción**        | **Ventajas**                                                                                                                        | **Desventajas**                                                                                                     |
|-------------------|-------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------|
| **SPA en React**  | Máxima flexibilidad visual e interactiva.                                                                                           | Suma un segundo ecosistema (TypeScript, build, manejo de estado, rutas, CORS). Es la opción más lenta de construir. |
| **Jinja2 + HTMX** | Un solo lenguaje; HTML generado por el servidor con actualizaciones parciales sin escribir JavaScript.                              | Hay que maquetar HTML y CSS a mano y diseñar cada interacción.                                                      |
| **Streamlit**     | Interfaz escrita en Python puro, con componentes listos (formularios, tablas, métricas, gráficos, pestañas). Sugerida por el tutor. | Menor control visual; la página se vuelve a ejecutar en cada interacción. No apta para un producto masivo.          |

**Decisión:** Streamlit, consumiendo la API REST de FastAPI. **Fundamento:** es la opción con menor tiempo de construcción para un desarrollador solo; el flujo del producto (formularios, listados, revisión y panel con métricas) encaja con sus componentes; la recomendó el tutor; y al dejar toda la lógica en la API se conserva la arquitectura full stack y una API documentada que puede mostrarse en la defensa.

### DEC-02 · Backend con FastAPI y PostgreSQL

FastAPI genera documentación OpenAPI/Swagger automática, valida entradas y salidas con Pydantic y soporta tareas en segundo plano. PostgreSQL con SQLAlchemy y Alembic da persistencia relacional con migraciones versionadas.

### DEC-03 · Proveedor de LLM intercambiable

El backend llama por HTTP (httpx) a un endpoint compatible con OpenAI, con base_url, modelo y clave configurables. Por defecto usa OpenRouter con el modelo deepseek/deepseek-v4.1-flash-1017, que da acceso a DeepSeek con una sola clave y un límite de crédito. Se pide salida JSON (response_format de tipo json_object), lo que exige mencionar “json” en el prompt e incluir un ejemplo del formato; se fija max_tokens para evitar respuestas truncadas y se excluye el razonamiento del modelo para ahorrar tokens y tiempo. Como la respuesta puede venir vacía o mal formada, se reintenta hasta 2 veces. DeepSeek directo u Ollama local se usan cambiando la configuración, y el modo demo usa respuestas pregrabadas. Se descartó el SDK de OpenAI porque es una sola llamada y httpx ya era dependencia del proyecto.

### DEC-04 · Generación híbrida con catálogo de pasos

El LLM recibe la historia y el catálogo de pasos del SUT, y devuelve escenarios cuyos pasos deben pertenecer al catálogo. El sistema valida cada paso con el patrón del catálogo y genera el código TypeScript con plantillas fijas. **Ventajas:** los scripts siempre son sintácticamente válidos y usan selectores correctos; el LLM no inyecta código; el proceso es trazable y testeable. **Costo aceptado:** la cobertura se limita a los pasos del catálogo, lo cual es razonable para un MVP.

### DEC-05 · Playwright Test con TypeScript

Es el lenguaje más difundido en el ecosistema Playwright. El backend (Python) genera los archivos .spec.ts y los ejecuta con npx playwright test y el reporter JSON. La imagen del backend incluye Python, Node.js y Chromium (parte de la imagen oficial de Playwright, mcr.microsoft.com/playwright:v1.64.1-noble, con la misma versión de \@playwright/test).

### DEC-06 · SauceDemo como aplicación objetivo

Sitio público de Sauce Labs pensado para practicar automatización. Ofrece usuarios de prueba documentados (por ejemplo standard_user y locked_out_user), atributos data-test estables y flujos de inicio de sesión, carrito y checkout que permiten escenarios positivos, negativos y de valores límite. Se consideró ParaBank por su temática bancaria, pero se descartó para el MVP porque depende de datos compartidos que cambian con frecuencia.

### DEC-07 · Ejecución en segundo plano

La ejecución se lanza desde el panel y corre como tarea en segundo plano de FastAPI (subproceso de Node). Se permite una sola ejecución a la vez, garantizado por un índice único parcial en la base. Playwright guarda capturas de pantalla solo en los fallos; las evidencias se almacenan en un volumen Docker y se sirven por la API. El frontend consulta el estado de la ejecución hasta que finaliza.

### DEC-08 · Protección del despliegue público

Como la autenticación está fuera de alcance, el acceso se protege a nivel de infraestructura con Cloudflare Access (código de acceso por correo, sin desarrollo adicional) y, en la aplicación, con un límite diario configurable de generaciones. Ambas medidas protegen la clave de la API del consumo indebido y se documentan como controles de seguridad.

## 4.4 Flujo principal de punta a punta

1.  El analista crea una historia de usuario (o elige una precargada).

2.  Solicita la generación. El backend arma el prompt con la historia y el catálogo, y llama al LLM.

3.  El backend valida la respuesta (JSON, Gherkin y catálogo) y guarda los casos como “pendientes”, marcando los inválidos.

4.  El analista revisa cada caso: lo edita (se revalida), lo aprueba o lo descarta.

5.  El analista exporta los casos aprobados: el backend genera el .spec.ts con plantillas y lo ofrece para descargar.

6.  El analista inicia la ejecución: el backend corre Playwright contra SauceDemo en segundo plano.

7.  El backend interpreta el reporte JSON de Playwright y guarda el resultado y las evidencias de cada caso.

8.  El panel muestra el resumen de la ejecución y el detalle de cada caso, con captura en los fallos.

# 5. Requerimientos funcionales

Cada requerimiento indica su prioridad, entradas, salidas, reglas y los criterios de aceptación asociados (sección 7).

### RF-01 · Gestión de historias de usuario

<table>
<colgroup>
<col style="width: 23%" />
<col style="width: 76%" />
</colgroup>
<thead>
<tr>
<th><strong>Prioridad</strong></th>
<th>Must</th>
</tr>
<tr>
<th><strong>Descripción</strong></th>
<th>Permite dar de alta, editar, listar y ver el detalle de historias de usuario.</th>
</tr>
<tr>
<th><strong>Entradas</strong></th>
<th><p>Título (obligatorio, hasta 120 caracteres).</p>
<p>Descripción en formato Como / quiero / para (obligatoria).</p>
<p>Criterios de aceptación en texto libre (opcional).</p></th>
</tr>
<tr>
<th><strong>Salidas</strong></th>
<th><p>Historia guardada con identificador (HU-n) y fechas de creación y actualización.</p>
<p>Listado con cantidad de casos por estado.</p></th>
</tr>
<tr>
<th><strong>Reglas</strong></th>
<th><p>El sistema incluye tres historias de ejemplo precargadas: inicio de sesión, carrito y checkout.</p>
<p>No se permite guardar sin título o sin descripción.</p></th>
</tr>
<tr>
<th><strong>Criterios</strong></th>
<th>CA-01</th>
</tr>
</thead>
<tbody>
</tbody>
</table>

### RF-02 · Catálogo de pasos de la aplicación objetivo

<table>
<colgroup>
<col style="width: 23%" />
<col style="width: 76%" />
</colgroup>
<thead>
<tr>
<th><strong>Prioridad</strong></th>
<th>Must</th>
</tr>
<tr>
<th><strong>Descripción</strong></th>
<th>Define los pasos Gherkin permitidos para SauceDemo, cada uno con su patrón y su plantilla de código Playwright.</th>
</tr>
<tr>
<th><strong>Entradas</strong></th>
<th>Archivo YAML versionado en el repositorio (ver Anexo D).</th>
</tr>
<tr>
<th><strong>Salidas</strong></th>
<th><p>Catálogo cargado al iniciar el backend.</p>
<p>Vista de solo lectura en la interfaz.</p>
<p>Lista de patrones incluida en el prompt.</p></th>
</tr>
<tr>
<th><strong>Reglas</strong></th>
<th><p>Cada paso tiene identificador único, patrón con parámetros entre llaves y plantilla.</p>
<p>Cobertura mínima: inicio de sesión, inventario, carrito y checkout.</p>
<p>Si el archivo es inválido, el backend no inicia y registra el error.</p></th>
</tr>
<tr>
<th><strong>Criterios</strong></th>
<th>CA-02</th>
</tr>
</thead>
<tbody>
</tbody>
</table>

### RF-03 · Generación de casos de prueba con IA

<table>
<colgroup>
<col style="width: 23%" />
<col style="width: 76%" />
</colgroup>
<thead>
<tr>
<th><strong>Prioridad</strong></th>
<th>Must</th>
</tr>
<tr>
<th><strong>Descripción</strong></th>
<th>Genera casos de prueba Gherkin en español a partir de una historia, usando el LLM configurado.</th>
</tr>
<tr>
<th><strong>Entradas</strong></th>
<th><p>Historia de usuario seleccionada.</p>
<p>Catálogo de pasos.</p>
<p>Versión del prompt.</p></th>
</tr>
<tr>
<th><strong>Salidas</strong></th>
<th><p>Entre 3 y 8 casos en estado “pendiente”, cada uno con título, tipo (positivo, negativo o límite) y pasos.</p>
<p>Registro de la generación (proveedor, modelo, versión del prompt, duración y resultado).</p></th>
</tr>
<tr>
<th><strong>Reglas</strong></th>
<th><p>Al menos un caso positivo y uno negativo por generación.</p>
<p>Ante una falla del proveedor se informa el error sin perder la historia.</p>
<p>Se respeta el límite diario de generaciones si está configurado.</p></th>
</tr>
<tr>
<th><strong>Criterios</strong></th>
<th>CA-03</th>
</tr>
</thead>
<tbody>
</tbody>
</table>

### RF-04 · Validación de la salida del modelo

<table>
<colgroup>
<col style="width: 23%" />
<col style="width: 76%" />
</colgroup>
<thead>
<tr>
<th><strong>Prioridad</strong></th>
<th>Must</th>
</tr>
<tr>
<th><strong>Descripción</strong></th>
<th>Verifica la respuesta del LLM antes de presentarla al usuario.</th>
</tr>
<tr>
<th><strong>Entradas</strong></th>
<th>Respuesta JSON del LLM.</th>
</tr>
<tr>
<th><strong>Salidas</strong></th>
<th>Casos válidos, o casos marcados como inválidos con el detalle del error (por ejemplo, el paso que no coincide).</th>
</tr>
<tr>
<th><strong>Reglas</strong></th>
<th><p>Valida el esquema JSON con Pydantic.</p>
<p>Cada caso es un único Escenario, sin Característica, Esquema ni tablas: el LLM devuelve la lista de pasos y el sistema arma el Escenario.</p>
<p>Valida la sintaxis Gherkin con el parser oficial.</p>
<p>Valida que cada paso coincida con un patrón del catálogo.</p>
<p>Si el JSON es inválido o viene vacío, reintenta hasta 2 veces; luego informa el error.</p></th>
</tr>
<tr>
<th><strong>Criterios</strong></th>
<th>CA-04</th>
</tr>
</thead>
<tbody>
</tbody>
</table>

### RF-05 · Revisión humana de casos

<table>
<colgroup>
<col style="width: 23%" />
<col style="width: 76%" />
</colgroup>
<thead>
<tr>
<th><strong>Prioridad</strong></th>
<th>Must</th>
</tr>
<tr>
<th><strong>Descripción</strong></th>
<th>Permite editar, aprobar o descartar cada caso generado.</th>
</tr>
<tr>
<th><strong>Entradas</strong></th>
<th><p>Caso seleccionado.</p>
<p>Texto Gherkin editado (en caso de edición).</p></th>
</tr>
<tr>
<th><strong>Salidas</strong></th>
<th>Caso con estado actualizado: pendiente, aprobado o descartado.</th>
</tr>
<tr>
<th><strong>Reglas</strong></th>
<th><p>Solo se aprueban casos válidos.</p>
<p>Toda edición se revalida (RF-04).</p>
<p>Un caso aprobado puede volver a “pendiente” para editarse.</p>
<p>Descartar es reversible solo volviendo a “pendiente”.</p></th>
</tr>
<tr>
<th><strong>Criterios</strong></th>
<th>CA-05</th>
</tr>
</thead>
<tbody>
</tbody>
</table>

### RF-06 · Exportación a Playwright (TypeScript)

<table>
<colgroup>
<col style="width: 23%" />
<col style="width: 76%" />
</colgroup>
<thead>
<tr>
<th><strong>Prioridad</strong></th>
<th>Must</th>
</tr>
<tr>
<th><strong>Descripción</strong></th>
<th>Genera un archivo .spec.ts con los casos aprobados de una historia.</th>
</tr>
<tr>
<th><strong>Entradas</strong></th>
<th>Historia con al menos un caso aprobado.</th>
</tr>
<tr>
<th><strong>Salidas</strong></th>
<th>Archivo HU-n.spec.ts descargable, con un test.describe por historia, un test por caso y un test.step por cada paso Gherkin.</th>
</tr>
<tr>
<th><strong>Reglas</strong></th>
<th><p>El código se genera solo con las plantillas del catálogo.</p>
<p>Los parámetros se insertan como literales de cadena escapados.</p>
<p>El título de cada test incluye el identificador del caso, por ejemplo [CP-12].</p>
<p>Si no hay casos aprobados, la exportación no está disponible.</p></th>
</tr>
<tr>
<th><strong>Criterios</strong></th>
<th>CA-06</th>
</tr>
</thead>
<tbody>
</tbody>
</table>

### RF-07 · Ejecución de pruebas

<table>
<colgroup>
<col style="width: 23%" />
<col style="width: 76%" />
</colgroup>
<thead>
<tr>
<th><strong>Prioridad</strong></th>
<th>Must</th>
</tr>
<tr>
<th><strong>Descripción</strong></th>
<th>Ejecuta los casos aprobados de una historia contra SauceDemo.</th>
</tr>
<tr>
<th><strong>Entradas</strong></th>
<th>Historia con al menos un caso aprobado.</th>
</tr>
<tr>
<th><strong>Salidas</strong></th>
<th>Ejecución registrada con estado (en curso, finalizada o con error), fechas de inicio y fin, y totales.</th>
</tr>
<tr>
<th><strong>Reglas</strong></th>
<th><p>Corre en segundo plano sin bloquear la interfaz.</p>
<p>Una sola ejecución a la vez; si hay otra en curso, se rechaza con un mensaje.</p>
<p>Chromium en modo headless con un tiempo máximo por prueba.</p></th>
</tr>
<tr>
<th><strong>Criterios</strong></th>
<th>CA-07</th>
</tr>
</thead>
<tbody>
</tbody>
</table>

### RF-08 · Registro de resultados y evidencias

<table>
<colgroup>
<col style="width: 23%" />
<col style="width: 76%" />
</colgroup>
<thead>
<tr>
<th><strong>Prioridad</strong></th>
<th>Must</th>
</tr>
<tr>
<th><strong>Descripción</strong></th>
<th>Guarda el resultado de cada caso ejecutado y sus evidencias.</th>
</tr>
<tr>
<th><strong>Entradas</strong></th>
<th>Reporte JSON de Playwright y capturas generadas.</th>
</tr>
<tr>
<th><strong>Salidas</strong></th>
<th>Resultado por caso: aprobado, fallido u omitido, duración, mensaje de error y captura (en fallos).</th>
</tr>
<tr>
<th><strong>Reglas</strong></th>
<th><p>El resultado se asocia al caso por el identificador incluido en el título del test.</p>
<p>Las capturas se sirven por la API.</p></th>
</tr>
<tr>
<th><strong>Criterios</strong></th>
<th>CA-08</th>
</tr>
</thead>
<tbody>
</tbody>
</table>

### RF-09 · Panel de historial y reporte

<table>
<colgroup>
<col style="width: 23%" />
<col style="width: 76%" />
</colgroup>
<thead>
<tr>
<th><strong>Prioridad</strong></th>
<th>Must</th>
</tr>
<tr>
<th><strong>Descripción</strong></th>
<th>Muestra el estado general y el detalle de historias, casos y ejecuciones.</th>
</tr>
<tr>
<th><strong>Entradas</strong></th>
<th>Datos persistidos.</th>
</tr>
<tr>
<th><strong>Salidas</strong></th>
<th><p>Por historia: casos por estado y resultado de la última ejecución.</p>
<p>Por ejecución: totales, porcentaje de éxito y detalle por caso con evidencias.</p></th>
</tr>
<tr>
<th><strong>Reglas</strong></th>
<th>Los datos se leen exclusivamente desde la API.</th>
</tr>
<tr>
<th><strong>Criterios</strong></th>
<th>CA-09</th>
</tr>
</thead>
<tbody>
</tbody>
</table>

### RF-10 · Modo demo

| **Prioridad**   | Should                                                                                                      |
|-----------------|-------------------------------------------------------------------------------------------------------------|
| **Descripción** | Permite generar casos sin llamar al proveedor, usando respuestas pregrabadas para las historias de ejemplo. |
| **Entradas**    | Variable de entorno LLM_PROVIDER=demo.                                                                      |
| **Salidas**     | Casos generados a partir de archivos JSON incluidos en el repositorio.                                      |
| **Reglas**      | Las respuestas pregrabadas pasan por la misma validación (RF-04).                                           |
| **Criterios**   | CA-10                                                                                                       |

### RF-11 · Regenerar casos de una historia

<table>
<colgroup>
<col style="width: 23%" />
<col style="width: 76%" />
</colgroup>
<thead>
<tr>
<th><strong>Prioridad</strong></th>
<th>Should</th>
</tr>
<tr>
<th><strong>Descripción</strong></th>
<th>Vuelve a ejecutar la generación para una historia existente.</th>
</tr>
<tr>
<th><strong>Entradas</strong></th>
<th>Historia con o sin casos previos.</th>
</tr>
<tr>
<th><strong>Salidas</strong></th>
<th>Nuevos casos pendientes.</th>
</tr>
<tr>
<th><strong>Reglas</strong></th>
<th><p>Los casos aprobados se conservan.</p>
<p>Los casos pendientes previos se reemplazan por los nuevos.</p></th>
</tr>
<tr>
<th><strong>Criterios</strong></th>
<th>CA-11</th>
</tr>
</thead>
<tbody>
</tbody>
</table>

### RF-12 · Historial de generaciones

| **Prioridad**   | Should                                                                                                               |
|-----------------|----------------------------------------------------------------------------------------------------------------------|
| **Descripción** | Muestra las generaciones realizadas por historia para trazabilidad.                                                  |
| **Entradas**    | Historia seleccionada.                                                                                               |
| **Salidas**     | Lista con fecha, proveedor, modelo, versión del prompt, duración, resultado y cantidad de casos válidos e inválidos. |
| **Reglas**      | Se registra incluso cuando la generación falla.                                                                      |
| **Criterios**   | CA-12                                                                                                                |

### Requerimientos opcionales (Could)

| **ID**    | **Nombre**                   | **Descripción**                                                                             |
|-----------|------------------------------|---------------------------------------------------------------------------------------------|
| **RF-13** | Métricas de calidad de la IA | Tasa de aprobación (aprobados / generados), descartados e inválidos, por historia y global. |
| **RF-14** | Trace de Playwright          | Guardar el trace en los fallos y ofrecerlo para descarga.                                   |
| **RF-15** | Exportación .zip             | Descargar un proyecto Playwright completo (configuración, package.json y specs).            |
| **RF-16** | Regenerar un caso puntual    | Pedir al LLM una nueva versión de un único caso.                                            |

# 6. Requerimientos no funcionales

| **ID**     | **Categoría**                 | **Requerimiento**                                                                                                                                                                          | **Prioridad** |
|------------|-------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|
| **RNF-01** | Idioma                        | Interfaz, mensajes y Gherkin en español (# language: es). Los textos propios del SUT se usan en su idioma original como parámetros.                                                        | Must          |
| **RNF-02** | Despliegue                    | Docker Compose con frontend, backend y base de datos; desplegado en Dokploy bajo un subdominio de ordema.app con HTTPS vía Cloudflare Tunnel; reproducible localmente con un solo comando. | Must          |
| **RNF-03** | Configuración                 | Toda la configuración por variables de entorno. El repositorio incluye un .env.example sin secretos.                                                                                       | Must          |
| **RNF-04** | Portabilidad del LLM          | Proveedor intercambiable por configuración (base_url, modelo y clave) sin cambiar código.                                                                                                  | Must          |
| **RNF-05** | Seguridad del código generado | El LLM nunca produce código ejecutable. Solo se usan pasos del catálogo y los parámetros se escapan como literales.                                                                        | Must          |
| **RNF-06** | Seguridad de secretos         | La clave de la API nunca se versiona ni se expone al frontend.                                                                                                                             | Must          |
| **RNF-07** | Control de acceso             | Acceso público protegido con Cloudflare Access.                                                                                                                                            | Should        |
| **RNF-08** | Control de consumo            | Límite diario configurable de generaciones (valor inicial sugerido: 30).                                                                                                                   | Should        |
| **RNF-09** | Uso responsable del SUT       | Ejecución solo manual, una a la vez, un único navegador y sin pruebas de carga.                                                                                                            | Must          |
| **RNF-10** | Privacidad                    | Solo historias y datos de ejemplo.                                                                                                                                                         | Must          |
| **RNF-11** | Rendimiento                   | Generación típica en 60 segundos o menos; ejecución de hasta 10 casos en 3 minutos o menos.                                                                                                | Should        |
| **RNF-12** | Documentación                 | README con instalación, configuración, uso y arquitectura; documentación OpenAPI automática en /docs.                                                                                      | Must          |
| **RNF-13** | Calidad interna               | Pruebas unitarias (pytest) del validador y del generador de código.                                                                                                                        | Should        |
| **RNF-14** | Observabilidad                | Registros (logs) de las llamadas al LLM y de las ejecuciones.                                                                                                                              | Could         |

# 7. Criterios de aceptación

Se expresan en Gherkin en español, el mismo formato que produce el producto. Cada bloque se vincula a un requerimiento funcional.

### CA-01 · RF-01 Gestión de historias

> Escenario: Alta de una historia válida
>
> Dado que estoy en la pantalla de historias
>
> Cuando cargo el título "Inicio de sesión" y una descripción
>
> Y guardo la historia
>
> Entonces la historia aparece en el listado con su identificador y fecha
>
> Escenario: Alta rechazada por título vacío
>
> Dado que estoy en la pantalla de historias
>
> Cuando intento guardar una historia sin título
>
> Entonces veo un mensaje que indica que el título es obligatorio
>
> Y la historia no se guarda

### CA-02 · RF-02 Catálogo de pasos

> Escenario: Consulta del catálogo
>
> Dado que el backend inició con un catálogo válido
>
> Cuando abro la pantalla del catálogo
>
> Entonces veo los pasos permitidos agrupados por funcionalidad
>
> Escenario: Catálogo inválido
>
> Dado un catálogo con dos pasos con el mismo identificador
>
> Cuando inicia el backend
>
> Entonces el inicio falla y se registra el error del catálogo

### CA-03 · RF-03 Generación con IA

> Escenario: Generación exitosa
>
> Dado una historia de usuario guardada
>
> Cuando solicito generar casos de prueba
>
> Entonces veo entre 3 y 8 casos en estado "pendiente"
>
> Y cada caso indica si es positivo, negativo o de valor límite
>
> Y hay al menos un caso positivo y uno negativo
>
> Escenario: El proveedor no responde
>
> Dado que el proveedor del LLM no está disponible
>
> Cuando solicito generar casos de prueba
>
> Entonces veo un mensaje de error comprensible
>
> Y la historia se conserva sin cambios
>
> Y el intento queda registrado en el historial de generaciones

### CA-04 · RF-04 Validación

> Escenario: Paso fuera del catálogo
>
> Dado que el modelo devuelve un caso con un paso que no está en el catálogo
>
> Cuando el sistema valida la respuesta
>
> Entonces el caso queda marcado como inválido
>
> Y se señala el paso que no coincide
>
> Escenario: Respuesta con formato inválido
>
> Dado que el modelo devuelve un JSON que no respeta el esquema
>
> Cuando el sistema valida la respuesta
>
> Entonces reintenta la generación hasta 2 veces
>
> Y si el error persiste lo informa al usuario

### CA-05 · RF-05 Revisión humana

> Escenario: Aprobar un caso válido
>
> Dado un caso válido en estado "pendiente"
>
> Cuando lo apruebo
>
> Entonces su estado pasa a "aprobado"
>
> Escenario: No se puede aprobar un caso inválido
>
> Dado un caso marcado como inválido
>
> Entonces la acción de aprobar no está disponible
>
> Escenario: Editar y revalidar
>
> Dado un caso inválido por un paso fuera del catálogo
>
> Cuando reemplazo el paso por uno del catálogo y guardo
>
> Entonces el caso se revalida y queda válido
>
> Escenario: Descartar un caso
>
> Dado un caso en estado "pendiente"
>
> Cuando lo descarto
>
> Entonces su estado pasa a "descartado" y no se exporta

### CA-06 · RF-06 Exportación

> Escenario: Exportar casos aprobados
>
> Dado una historia con 3 casos aprobados y 2 descartados
>
> Cuando exporto los casos
>
> Entonces descargo un archivo .spec.ts con 3 pruebas
>
> Y el título de cada prueba incluye el identificador del caso
>
> Y el archivo compila sin errores con "tsc --noEmit"
>
> Escenario: Historia sin casos aprobados
>
> Dado una historia sin casos aprobados
>
> Entonces la exportación no está disponible

### CA-07 · RF-07 Ejecución

> Escenario: Ejecutar las pruebas de una historia
>
> Dado una historia con casos aprobados
>
> Cuando inicio la ejecución
>
> Entonces la ejecución aparece "en curso" y luego "finalizada"
>
> Y puedo seguir usando la interfaz mientras corre
>
> Escenario: Evitar ejecuciones simultáneas
>
> Dado una ejecución en curso
>
> Cuando intento iniciar otra
>
> Entonces veo un mensaje que indica que ya hay una ejecución en curso

### CA-08 · RF-08 Resultados y evidencias

> Escenario: Caso fallido con evidencia
>
> Dado una ejecución finalizada con un caso fallido
>
> Cuando abro el detalle de la ejecución
>
> Entonces veo el mensaje de error del caso
>
> Y veo la captura de pantalla tomada en el fallo

### CA-09 · RF-09 Panel

> Escenario: Resumen en el panel
>
> Dado historias con casos y ejecuciones registradas
>
> Cuando abro el panel
>
> Entonces veo por historia la cantidad de casos por estado
>
> Y el resultado de su última ejecución
>
> Y para cada ejecución el total de aprobados, fallidos y el porcentaje de éxito

### CA-10 · RF-10 Modo demo

> Escenario: Generación en modo demo
>
> Dado que el sistema está configurado en modo demo
>
> Cuando solicito generar casos para una historia de ejemplo
>
> Entonces obtengo los casos sin llamar al proveedor del LLM

### CA-11 · RF-11 Regeneración

> Escenario: Regenerar conservando los aprobados
>
> Dado una historia con 2 casos aprobados y 3 pendientes
>
> Cuando regenero los casos
>
> Entonces los 2 casos aprobados se conservan
>
> Y los 3 pendientes se reemplazan por los nuevos casos

### CA-12 · RF-12 Historial y RNF-08 Límite

> Escenario: Historial de generaciones
>
> Dado una historia con dos generaciones realizadas
>
> Cuando abro su historial
>
> Entonces veo fecha, modelo, versión del prompt, duración y resultado de cada una
>
> Escenario: Límite diario alcanzado
>
> Dado que se alcanzó el límite diario de generaciones
>
> Cuando solicito generar casos
>
> Entonces veo un mensaje que indica que se alcanzó el límite
>
> Y no se llama al proveedor del LLM

# 8. Modelo de datos

Modelo relacional en PostgreSQL. El catálogo de pasos no se guarda en la base: vive en el repositorio y se versiona con Git.

| **Entidad**          | **Atributos principales**                                                                                                                                                                                         | **Relaciones**                                        |
|----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------|
| **historia_usuario** | id, titulo, descripcion, criterios_aceptacion, creada_en, actualizada_en                                                                                                                                          | 1:N generacion, caso_prueba y ejecucion               |
| **generacion**       | id, historia_id, proveedor, modelo, version_prompt, estado (ok \| error), duracion_ms, respuesta_cruda (JSONB), mensaje_error, casos_validos, casos_invalidos, creada_en                                          | N:1 historia_usuario; 1:N caso_prueba                 |
| **caso_prueba**      | id, historia_id, generacion_id (admite nulo), titulo, tipo (positivo \| negativo \| limite), gherkin, estado (pendiente \| aprobado \| descartado), valido, errores_validacion (JSONB), creado_en, actualizado_en | N:1 historia_usuario y generacion; 1:N resultado_caso |
| **ejecucion**        | id, historia_id, estado (en_curso \| finalizada \| error), iniciada_en, finalizada_en, total, aprobados, fallidos, omitidos, log                                                                                  | N:1 historia_usuario; 1:N resultado_caso              |
| **resultado_caso**   | id, ejecucion_id, caso_id (admite nulo), estado (aprobado \| fallido \| omitido), duracion_ms, mensaje_error, ruta_captura                                                                                        | N:1 ejecucion y caso_prueba                           |

caso_prueba.generacion_id y resultado_caso.caso_id usan ON DELETE SET NULL: un caso aprobado sobrevive aunque se borre su generación, y regenerar los casos de una historia no borra los resultados de ejecuciones pasadas. Un índice único parcial sobre ejecucion.estado garantiza una sola ejecución en curso.

## 8.1 Estados del caso de prueba

> (generación) --\> pendiente
>
> pendiente --(aprobar, solo si es válido)--\> aprobado
>
> pendiente --(descartar)-------------------\> descartado
>
> aprobado --(volver a pendiente)----------\> pendiente
>
> descartado --(volver a pendiente)----------\> pendiente
>
> La edición solo se permite en "pendiente" y siempre revalida el caso.

# 9. Interfaces

## 9.1 API REST

| **Método** | **Ruta**                                      | **Descripción**                                                   | **RF**              |
|------------|-----------------------------------------------|-------------------------------------------------------------------|---------------------|
| GET        | /historias                                    | Listar historias con resumen de casos.                            | RF-01, RF-09        |
| POST       | /historias                                    | Crear historia.                                                   | RF-01               |
| GET / PUT  | /historias/{id}                               | Ver o editar una historia.                                        | RF-01               |
| GET        | /catalogo                                     | Obtener el catálogo de pasos.                                     | RF-02               |
| POST       | /historias/{id}/generaciones                  | Generar (o regenerar) casos con IA.                               | RF-03, RF-04, RF-11 |
| GET        | /historias/{id}/generaciones                  | Historial de generaciones.                                        | RF-12               |
| GET        | /historias/{id}/casos                         | Listar casos de una historia.                                     | RF-05               |
| PUT        | /casos/{id}                                   | Editar el Gherkin de un caso (revalida).                          | RF-05               |
| POST       | /casos/{id}/aprobar \| descartar \| pendiente | Cambiar el estado de un caso.                                     | RF-05               |
| GET        | /historias/{id}/export                        | Descargar el .spec.ts de los casos aprobados.                     | RF-06               |
| POST       | /historias/{id}/ejecuciones                   | Iniciar una ejecución.                                            | RF-07               |
| GET        | /ejecuciones, /ejecuciones/{id}               | Listar ejecuciones o ver su detalle y resultados.                 | RF-08, RF-09        |
| GET        | /evidencias/{resultado_id}                    | Obtener la captura de pantalla de un resultado.                   | RF-08               |
| GET        | /salud                                        | Estado del servicio, la base de datos y la configuración del LLM. | RNF-12              |

## 9.2 Pantallas

| **Pantalla**            | **Contenido**                                                                          |
|-------------------------|----------------------------------------------------------------------------------------|
| **Panel**               | Métricas generales, historias con casos por estado y últimas ejecuciones.              |
| **Historias**           | Listado, alta y edición de historias.                                                  |
| **Detalle de historia** | Generar o regenerar, revisar casos (editar, aprobar o descartar), exportar y ejecutar. |
| **Ejecuciones**         | Listado y detalle con resultado por caso y capturas.                                   |
| **Catálogo**            | Pasos permitidos del SUT (solo lectura).                                               |
| **Acerca de**           | Descripción del producto, proveedor y modelo configurados, enlace a /docs.             |

## 9.3 Integración con el LLM

- **Entrada:** prompt de sistema versionado (rol, reglas, catálogo y ejemplo de JSON) más la historia del usuario. Ver Anexo A.

- **Parámetros: response_format json_object, temperatura 0,2, max_tokens 8000 y razonamiento del modelo excluido.**

- **Salida esperada:** objeto JSON con la lista de casos (título, tipo y pasos). Ver Anexo B.

- **Manejo de errores: tiempo máximo de 90 s por llamada, hasta 2 reintentos ante JSON vacío o inválido, y registro de cada intento en generacion.**

## 9.4 Integración con Playwright

- El backend contiene un proyecto plantilla (playwright.config.ts y package.json) con baseURL de SauceDemo, Chromium headless, screenshot: "only-on-failure" y tiempo máximo por prueba.

- Para cada ejecución se escribe el .spec.ts en un directorio de trabajo y se ejecuta npx playwright test --reporter=json.

- El reporte JSON se interpreta y cada test se asocia a su caso por el identificador \[CP-n\] del título.

# 10. Riesgos y mitigaciones

| **ID**   | **Riesgo**                                                | **Impacto** | **Mitigación**                                                                                                                                                              |
|----------|-----------------------------------------------------------|-------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **R-01** | El LLM genera pasos fuera del catálogo o JSON inválido.   | Medio       | Validación (RF-04), reintentos, ejemplos en el prompt y edición manual.                                                                                                     |
| **R-02** | La API del LLM falla o se demora durante la demo en vivo. | Alto        | Modo demo (RF-10), datos ya generados en la base y demo pregrabada.                                                                                                         |
| **R-03** | SauceDemo cambia sus selectores o no está disponible.     | Alto        | Selectores centralizados en el catálogo; verificación antes de la defensa; demo pregrabada; evaluar alojar una copia local (Sauce Labs publica el código de la aplicación). |
| **R-04** | El alcance no entra en el tiempo disponible.              | Alto        | MoSCoW, esqueleto funcional de punta a punta en S3, congelamiento de funcionalidades el 22/11.                                                                              |
| **R-05** | Costo o consumo indebido de la API.                       | Medio       | Proveedor económico, límite diario y Cloudflare Access.                                                                                                                     |
| **R-06** | Dependencias de Playwright dentro del contenedor.         | Medio       | Usar la imagen oficial de Playwright; validar el contenedor en S3.                                                                                                          |
| **R-07** | Un modelo local no alcanza la calidad necesaria.          | Bajo        | DeepSeek por defecto; el modelo local queda como alternativa.                                                                                                               |
| **R-08** | El tutor objeta el uso de un SUT de terceros.             | Medio       | Comunicar el cambio de inmediato; el catálogo permite apuntar a otra app con poco esfuerzo.                                                                                 |

# 11. Plan de trabajo

Replanificación desde el 19/10/2026. Al final de cada semana se registra el avance en la bitácora.

| **Semana** | **Período**   | **Objetivo**                                                                                                                                                                                            | **Hito o entregable**                                                        |
|------------|---------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **S3**     | 19/10 – 25/10 | Spec cerrado (v1.0). Repositorio, Docker Compose, PostgreSQL, modelo de datos y migraciones. CRUD de historias (RF-01) y esqueleto en Streamlit. Primer despliegue en Dokploy. Diagramas UML iniciales. | Esqueleto desplegado y accesible.                                            |
| **S4**     | 26/10 – 01/11 | Catálogo de SauceDemo (RF-02). Integración con DeepSeek, prompt v1, generación (RF-03) y validación (RF-04). Revisión humana (RF-05).                                                                   | Casos generados y validados desde la interfaz.                               |
| **S5**     | 02/11 – 08/11 | Generador TypeScript (RF-06), runner de Playwright (RF-07) y resultados con capturas (RF-08).                                                                                                           | **Segundo encuentro (alrededor del 50 %):** flujo completo de punta a punta. |
| **S6**     | 09/11 – 15/11 | Panel y reportes (RF-09). Modo demo, regeneración e historial (RF-10 a RF-12). Cloudflare Access y límite diario.                                                                                       | MVP completo.                                                                |
| **S7**     | 16/11 – 22/11 | Pruebas unitarias, corrección de errores, README, presentación comercial y técnica, demo pregrabada. **Congelamiento de funcionalidades el 22/11.**                                                     | **Tercer encuentro (alrededor del 75 %).**                                   |
| **S8**     | 23/11 – 26/11 | Verificación final del despliegue y de SauceDemo, ensayo de la defensa.                                                                                                                                 | **Defensa: 26/11/2026.**                                                     |

Ejecución real: S3 cumplió su objetivo salvo el primer despliegue, que se hizo el 04/11 en S4. S4 cerró el 05/11, con 4 días de atraso, pero adelantó Cloudflare Access, el límite diario, el modo demo y la regeneración, previstos para S6. S5 cerró el mismo 05/11 y recuperó el atraso. S6 cerró el 14/11 con todos los requerimientos Must y Should implementados. El detalle semanal está en la bitácora.

Fecha alternativa: si hay un desvío importante, el lineamiento de la cátedra indica reconfirmar la fecha de final; la siguiente mesa es el 17/12/2026.

# 12. Entregables académicos

| **Entregable (lineamientos)**                     | **Contenido en este proyecto**                                                                                                                                                             | **Semana** |
|---------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------|
| **Ficha técnica (Word)**                          | Propuesta aprobada, actualizada con los cambios de la sección 2.6.                                                                                                                         | S3         |
| **Presentación comercial**                        | Problema, propuesta de valor, público objetivo (equipos de QA, sectores regulados), diferenciales y referencias del mercado. Se acompaña con la landing del producto (landing/index.html). | S7         |
| **Presentación técnica: bitácora de avance**      | Registro semanal de lo hecho, problemas y decisiones.                                                                                                                                      | Continuo   |
| **Presentación técnica: herramientas utilizadas** | Stack de la sección 4.2 y herramientas de IA de la sección 13.                                                                                                                             | S7         |
| **Presentación técnica: diagramas UML**           | Casos de uso, clases (modelo de dominio), secuencia (generación y ejecución), estados del caso de prueba y componentes y despliegue.                                                       | S3 a S7    |
| **Repositorio y README.md**                       | Código fuente, catálogo, .env.example y README con documentación técnica.                                                                                                                  | Continuo   |
| **Demo pregrabada**                               | Video del flujo completo de punta a punta.                                                                                                                                                 | S7         |
| **Muestra en vivo**                               | Flujo completo sobre el despliegue en ordema.app, con el modo demo como respaldo.                                                                                                          | S8         |

# 13. Uso de inteligencia artificial en el desarrollo

La cátedra permite el uso (no abuso) de la IA siempre que se declaren las herramientas utilizadas. Se distinguen dos usos:

| **Uso**                         | **Herramienta**                       | **Finalidad**                                                                                                                                                          |
|---------------------------------|---------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Componente del producto**     | DeepSeek a través de OpenRouter (API) | Proponer casos de prueba, siempre sujetos a validación y aprobación humana.                                                                                            |
| **Asistencia en el desarrollo** | Claude (Anthropic)                    | Análisis de requisitos y redacción de este documento.                                                                                                                  |
| **Asistencia en el desarrollo** | Claude Code (Anthropic)               | Agente de código: implementación por fases a partir de este documento, con un plan aprobado por el autor antes de cada fase, pruebas automáticas y un commit por fase. |

# 14. Matriz de trazabilidad

| **RF**    | **Prioridad** | **Criterio** | **Componente principal**                  | **Semana** |
|-----------|---------------|--------------|-------------------------------------------|------------|
| **RF-01** | Must          | CA-01        | API historias + pantalla Historias        | S3         |
| **RF-02** | Must          | CA-02        | Catálogo YAML + cargador                  | S4         |
| **RF-03** | Must          | CA-03        | Servicio de generación IA                 | S4         |
| **RF-04** | Must          | CA-04        | Validador (Pydantic, Gherkin, catálogo)   | S4         |
| **RF-05** | Must          | CA-05        | API casos + pantalla Detalle de historia  | S4         |
| **RF-06** | Must          | CA-06        | Exportador (plantillas del catálogo → TS) | S5         |
| **RF-07** | Must          | CA-07        | Runner Playwright                         | S5         |
| **RF-08** | Must          | CA-08        | Parser de reporte + evidencias            | S5         |
| **RF-09** | Must          | CA-09        | Pantallas Panel y Ejecuciones             | S6         |
| **RF-10** | Should        | CA-10        | Proveedor “demo” del servicio IA          | S6         |
| **RF-11** | Should        | CA-11        | Servicio de generación IA                 | S6         |
| **RF-12** | Should        | CA-12        | Entidad generacion + vista historial      | S6         |

# 15. Pendientes y preguntas abiertas

- Comunicar al tutor el cambio de aplicación objetivo (SauceDemo) y la elección de Streamlit.

- Crear la cuenta y la clave del proveedor del LLM. Resuelto: clave de OpenRouter con límite de crédito; una generación real tarda entre 6 y 12 s.

- Verificar los selectores de SauceDemo al construir el catálogo. Resuelto: verificados el 04/11/2026 y el 05/11/2026 (catálogo v2).

- Definir los subdominios de ordema.app para el frontend y la API. Resuelto: qa.ordema.app y qa-api.ordema.app.

- Definir el agente de código. Resuelto: Claude Code (sección 13).

- Completar matrícula y celular en la ficha técnica.

# Anexo A · Estructura del prompt (v1)

El prompt de sistema se versiona en el repositorio y su versión se guarda en cada generación.

> Rol: analista QA senior especializado en diseño de casos de prueba.
>
> Reglas:
>
> \- Respondé SOLO con un objeto json con la estructura del ejemplo.
>
> \- Escribí en español. Generá entre 3 y 8 casos.
>
> \- Incluí casos positivos, negativos y de valores límite cuando apliquen.
>
> \- Cada paso debe comenzar con Dado, Cuando, Entonces, Y o Pero
>
> y su texto debe coincidir con un patrón del catálogo.
>
> \- Reemplazá los parámetros {texto} por valores concretos entre comillas.
>
> \- Usá solo los valores reales de la aplicación. No inventes pasos.
>
> Catálogo de pasos permitidos:
>
> \<lista de patrones del catálogo\>
>
> Datos de la aplicación (bloque «contexto» del catálogo):
>
> \<usuarios, mensajes, productos y títulos verificados\>
>
> Ejemplo de salida json:
>
> \<ejemplo del Anexo B\>
>
> Historia de usuario:
>
> \<título, descripción y criterios de aceptación\>

# Anexo B · Ejemplo de salida del LLM

> {
>
> "casos": \[
>
> {
>
> "titulo": "Ingreso exitoso con usuario estándar",
>
> "tipo": "positivo",
>
> "pasos": \[
>
> "Dado que estoy en la página de inicio de sesión",
>
> "Cuando ingreso el usuario \\"standard_user\\"",
>
> "Y ingreso la contraseña \\"secret_sauce\\"",
>
> "Y presiono el botón de ingresar",
>
> "Entonces veo el listado de productos"
>
> \]
>
> },
>
> {
>
> "titulo": "Ingreso rechazado para usuario bloqueado",
>
> "tipo": "negativo",
>
> "pasos": \[ "..." \]
>
> }
>
> \]
>
> }

# Anexo C · Del Gherkin al script

## C.1 Caso aprobado (CP-12 de la historia HU-1)

> Escenario: Ingreso exitoso con usuario estándar
>
> Dado que estoy en la página de inicio de sesión
>
> Cuando ingreso el usuario "standard_user"
>
> Y ingreso la contraseña "secret_sauce"
>
> Y presiono el botón de ingresar
>
> Entonces veo el listado de productos

## C.2 Script generado (HU-1.spec.ts)

> // Generado por Casewright para HU-1 (catálogo saucedemo v2).
>
> // Cada paso Gherkin se traduce con la plantilla del catálogo; no editar a mano.
>
> import { test, expect } from '@playwright/test';
>
> test.describe("\[HU-1\] Inicio de sesión", () =\> {
>
> test("\[CP-12\] Ingreso exitoso con usuario estándar", async ({ page }) =\> {
>
> await test.step("Dado que estoy en la página de inicio de sesión", async () =\> {
>
> await page.goto('/');
>
> });
>
> await test.step("Cuando ingreso el usuario \\"standard_user\\"", async () =\> {
>
> await page.locator('\[data-test="username"\]').fill("standard_user");
>
> });
>
> await test.step("Y ingreso la contraseña \\"secret_sauce\\"", async () =\> {
>
> await page.locator('\[data-test="password"\]').fill("secret_sauce");
>
> });
>
> await test.step("Y presiono el botón de ingresar", async () =\> {
>
> await page.locator('\[data-test="login-button"\]').click();
>
> });
>
> await test.step("Entonces veo el listado de productos", async () =\> {
>
> await expect(page.locator('\[data-test="inventory-container"\]')).toBeVisible();
>
> });
>
> });
>
> });

# Anexo D · Ejemplo del catálogo de pasos

Extracto del catálogo real (backend/catalogo/saucedemo.yaml, versión 2, 29 pasos). Los selectores se verificaron contra SauceDemo el 04/11/2026 y el 05/11/2026.

> sut: saucedemo
>
> base_url: https://www.saucedemo.com
>
> version: 2
>
> contexto: \|-
>
> Usuarios: standard_user (normal), locked_out_user (bloqueado), ...
>
> Mensajes de error del inicio de sesión:
>
> \- "Epic sadface: Username is required"
>
> ...
>
> pasos:
>
> \- id: abrir_login
>
> grupo: inicio de sesión
>
> patron: que estoy en la página de inicio de sesión
>
> plantilla: \|-
>
> await page.goto('/');
>
> \- id: ingresar_usuario
>
> grupo: inicio de sesión
>
> patron: ingreso el usuario "{texto}"
>
> plantilla: \|-
>
> await page.locator('\[data-test="username"\]').fill({texto});
>
> \- id: ver_error
>
> grupo: general
>
> patron: veo el mensaje de error "{texto}"
>
> plantilla: \|-
>
> await expect(page.locator('\[data-test="error"\]')).toContainText({texto});
>
> \- id: ver_productos
>
> grupo: inventario
>
> patron: veo el listado de productos
>
> plantilla: \|-
>
> await expect(page.locator('\[data-test="inventory-container"\]')).toBeVisible();
