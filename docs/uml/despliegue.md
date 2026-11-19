# Diagrama de componentes y despliegue

Despliegue en el servidor propio (Proxmox + Dokploy) con Docker Compose, publicado mediante Cloudflare Tunnel (spec, sección 4 y RNF-02). Muestra los cuatro contenedores, sus volúmenes y los servicios externos. La landing es pública; la interfaz y la API están detrás de Cloudflare Access.

```mermaid
flowchart TB
    nav["Navegador<br/>Analista QA"]
    visitante["Navegador<br/>Visitante"]

    subgraph cloudflare["Cloudflare"]
        tunel["Cloudflare Tunnel<br/>HTTPS + WebSockets<br/>Cloudflare Access"]
    end

    subgraph servidor["Servidor propio · Proxmox + Dokploy"]
        subgraph compose["Docker Compose"]
            fe["frontend<br/>Streamlit · puerto 8501"]
            be["backend<br/>FastAPI + Alembic<br/>Node.js + Playwright + Chromium<br/>puerto 8000"]
            db[("db<br/>PostgreSQL 16<br/>sin puerto publicado")]
            landing["landing<br/>nginx · HTML estático · puerto 80"]
        end
        pgdata[("volumen pgdata")]
        evidencias[("volumen evidencias<br/>/data/evidencias")]
    end

    llm["API LLM<br/>OpenRouter (DeepSeek)"]
    sut["SauceDemo<br/>saucedemo.com"]

    nav -->|HTTPS| tunel
    tunel -->|"subdominio del frontend"| fe
    tunel -->|"subdominio de la API (/docs)"| be
    visitante -->|HTTPS| tunel
    tunel -->|"subdominio de la landing<br/>(pública, sin Access)"| landing
    fe -->|"REST/JSON · red interna"| be
    be -->|SQL| db
    db --- pgdata
    be --- evidencias
    be -->|HTTPS| llm
    be -->|"HTTPS · Chromium headless"| sut
```
