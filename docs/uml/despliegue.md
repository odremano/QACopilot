# Diagrama de componentes y despliegue

Despliegue en el servidor propio (Proxmox + Dokploy) con Docker Compose, publicado mediante Cloudflare Tunnel (spec, sección 4 y RNF-02). Muestra los tres contenedores, sus volúmenes y los servicios externos.

```mermaid
flowchart TB
    nav["Navegador<br/>Analista QA"]

    subgraph cloudflare["Cloudflare"]
        tunel["Cloudflare Tunnel<br/>HTTPS + WebSockets<br/>Access (S6)"]
    end

    subgraph servidor["Servidor propio · Proxmox + Dokploy"]
        subgraph compose["Docker Compose"]
            fe["frontend<br/>Streamlit · puerto 8501"]
            be["backend<br/>FastAPI + Alembic<br/>Node.js + Playwright + Chromium<br/>puerto 8000"]
            db[("db<br/>PostgreSQL 16<br/>sin puerto publicado")]
        end
        pgdata[("volumen pgdata")]
        evidencias[("volumen evidencias<br/>/data/evidencias")]
    end

    llm["API LLM<br/>DeepSeek / Ollama"]
    sut["SauceDemo<br/>saucedemo.com"]

    nav -->|HTTPS| tunel
    tunel -->|"subdominio del frontend"| fe
    tunel -->|"subdominio de la API (/docs)"| be
    fe -->|"REST/JSON · red interna"| be
    be -->|SQL| db
    db --- pgdata
    be --- evidencias
    be -->|"HTTPS (S4)"| llm
    be -->|"HTTPS · Chromium headless (S5)"| sut
```
