# Imagen oficial de Playwright: trae Node.js, Chromium y sus dependencias del sistema (R-06).
# El tag debe coincidir exactamente con la versión de @playwright/test en playwright/package.json.
FROM mcr.microsoft.com/playwright:v1.64.1-noble

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    NPM_CONFIG_UPDATE_NOTIFIER=false \
    PATH="/opt/venv/bin:$PATH"

# 1) Dependencias del sistema: Python 3.12 de Ubuntu noble + venv.
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-venv \
    && rm -rf /var/lib/apt/lists/*

# 2) Virtualenv y dependencias de Python (noble bloquea pip global por PEP 668).
WORKDIR /app
RUN python3 -m venv /opt/venv
COPY pyproject.toml ./
RUN pip install ".[dev]"

# 3) Dependencias de Node para Playwright (los navegadores ya vienen en la imagen).
COPY playwright/package.json playwright/package-lock.json ./playwright/
RUN cd playwright && npm ci --no-audit --no-fund

# 4) Código de la aplicación.
COPY . .
RUN sed -i 's/\r$//' docker-entrypoint.sh \
    && chmod +x docker-entrypoint.sh \
    && mkdir -p /data/evidencias \
    && chown -R pwuser:pwuser /app /data/evidencias

USER pwuser

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/salud', timeout=4)" || exit 1

ENTRYPOINT ["./docker-entrypoint.sh"]
