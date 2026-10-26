# Despliegue en Dokploy

Guía para desplegar QA Copilot en el servidor propio (Proxmox + Dokploy) como aplicación **Docker Compose** desde el repositorio de GitHub, publicada con **Cloudflare Tunnel** bajo `ordema.app` (RNF-02).

> Reemplazá `<frontend>` y `<api>` por los subdominios elegidos (por ejemplo, `qa` y `qa-api`). La spec deja su definición como pendiente (sección 15).

## 1. Requisitos previos

- El repositorio subido a GitHub (sin `.env`: está en `.gitignore`).
- Dokploy con acceso a la cuenta de GitHub (Settings → Git → GitHub).
- `cloudflared` corriendo en el servidor con un túnel ya creado para `ordema.app`.
- Dos puertos libres en el servidor para publicar el backend y el frontend. Para ver los que ya están en uso: `ss -ltnp`.

## 2. Crear la aplicación en Dokploy

1. **Projects → Create Project** (por ejemplo, `qa-copilot`).
2. Dentro del proyecto: **Create Service → Compose**.
3. En **General**:
   - Provider: **GitHub**; repositorio `qa-copilot`; rama `main`.
   - Compose Path: `./docker-compose.yml`.
   - Compose Type: **Docker Compose**.
4. No hace falta configurar **Domains** en Dokploy: el tráfico entra por Cloudflare Tunnel a los puertos publicados. El compose no usa `container_name`, así que no hay conflictos de nombres.

## 3. Variables de entorno

En la pestaña **Environment** del servicio, cargá las mismas variables que en `.env.example`. Dokploy las escribe en un archivo `.env` junto al compose, que es el que leen `env_file: .env` y la interpolación de puertos.

```dotenv
POSTGRES_DB=qa_copilot
POSTGRES_USER=qa_copilot
POSTGRES_PASSWORD=<contraseña larga y aleatoria>
DATABASE_URL=postgresql+psycopg://qa_copilot:<la misma contraseña>@db:5432/qa_copilot

API_BASE_URL=http://backend:8000
API_PUBLIC_URL=https://<api>.ordema.app

BACKEND_PORT=<puerto libre, p. ej. 18000>
FRONTEND_PORT=<puerto libre, p. ej. 18501>

SEED_EXAMPLES=true
LOG_LEVEL=INFO

# A partir de S4:
# LLM_PROVIDER=deepseek
# LLM_BASE_URL=https://api.deepseek.com
# LLM_MODEL=deepseek-chat
# LLM_API_KEY=<clave de DeepSeek>
# DAILY_GENERATION_LIMIT=30
# A partir de S5:
# SUT_BASE_URL=https://www.saucedemo.com
```

Notas:

- **Contraseña de la base:** PostgreSQL la fija solo la primera vez que crea el volumen `pgdata`. Si después la cambiás en las variables, también tenés que cambiarla adentro de la base (`ALTER USER qa_copilot PASSWORD '...'`) o borrar el volumen (se pierden los datos).
- Si la contraseña tiene caracteres especiales (`@`, `:`, `/`, `%`), codificalos en `DATABASE_URL` (por ejemplo, `@` → `%40`), o usá una contraseña alfanumérica.
- `API_BASE_URL` siempre apunta a la red interna (`http://backend:8000`). `API_PUBLIC_URL` es solo el enlace a `/docs` que muestra la pantalla "Acerca de".
- `LLM_API_KEY` vive solo en Dokploy: nunca se versiona ni llega al frontend (RNF-06).

Después, **Deploy**. El primer build tarda varios minutos porque descarga la imagen de Playwright (~2 GB). Para seguir el avance, mirá la pestaña **Logs**, donde tienen que aparecer "Aplicando migraciones...", "Se cargaron 3 historias de ejemplo." e "Iniciando la API...".

## 4. Cloudflare Tunnel

En **Cloudflare Zero Trust → Networks → Tunnels → (tu túnel) → Public Hostname**, agregá dos hostnames:

| Subdominio | Dominio | Servicio |
|---|---|---|
| `<frontend>` | `ordema.app` | `http://localhost:<FRONTEND_PORT>` |
| `<api>` | `ordema.app` | `http://localhost:<BACKEND_PORT>` |

Si `cloudflared` corre en otra VM o contenedor, reemplazá `localhost` por la IP del servidor donde corre Dokploy.

**WebSockets:** Streamlit se comunica con el navegador por WebSocket (`/_stcore/stream`). Cloudflare Tunnel lo soporta, pero verificá que **WebSockets** esté habilitado en el panel del dominio (**Network → WebSockets**). Si la interfaz queda en "Connecting..." o se reconecta todo el tiempo, este es el primer lugar a revisar.

Si agregás o cambiás el subdominio de la API, actualizá `API_PUBLIC_URL` en Dokploy y volvé a desplegar (o reiniciá solo el frontend).

## 5. Checklist de verificación post-deploy

- [ ] En Dokploy, los tres contenedores aparecen *running* y `backend` y `frontend` en estado *healthy*.
- [ ] `https://<api>.ordema.app/salud` responde `{"estado": "ok", "base_de_datos": "ok", ...}`.
- [ ] `https://<api>.ordema.app/docs` muestra Swagger con las secciones "Historias" y "Salud".
- [ ] `https://<frontend>.ordema.app` abre el Panel con **3 historias**.
- [ ] En **Historias**, dar de alta una historia nueva: aparece en el listado con su código `HU-n`.
- [ ] Intentar guardar sin título: aparece "El título es obligatorio." y no se guarda.
- [ ] **Acerca de** muestra la base "OK" y el enlace a `/docs` apunta al subdominio público.
- [ ] Opcional: desde la terminal del servidor, `docker exec <contenedor-backend> sh -c "cd playwright && npx playwright test smoke"` pasa (Chromium funciona en el servidor).

## 6. Pendiente (S6): Cloudflare Access

Hasta S6 la aplicación queda pública y sin autenticación (fuera de alcance, DEC-08). En S6 se agrega una aplicación de **Cloudflare Access** que cubra ambos hostnames, con política de código de acceso por correo (RNF-07). Si querés limitar la exposición antes, podés activar Access desde el primer despliegue: no requiere cambios en el código.
