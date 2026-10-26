#!/bin/sh
# Arranque del backend: migraciones, datos de ejemplo y servidor.
set -e

# depends_on con service_healthy ya espera a la base; este reintento cubre
# despliegues donde esa condición no se respeta (por ejemplo, reinicios aislados).
python - <<'EOF'
import sys
import time

import psycopg

from app.config import settings

url = settings.database_url.replace("postgresql+psycopg://", "postgresql://")
for intento in range(1, 16):
    try:
        psycopg.connect(url, connect_timeout=3).close()
        break
    except psycopg.OperationalError:
        print(f"Esperando la base de datos (intento {intento}/15)...", flush=True)
        time.sleep(2)
else:
    sys.exit("No se pudo conectar con la base de datos.")
EOF

echo "Aplicando migraciones..."
alembic upgrade head

if [ "${SEED_EXAMPLES:-true}" = "true" ]; then
    echo "Cargando historias de ejemplo..."
    python -m app.seed
fi

echo "Iniciando la API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
