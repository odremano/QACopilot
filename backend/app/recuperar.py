"""Al arrancar el backend: marca como error las ejecuciones que un reinicio dejó «en curso».

Si no, la regla de una ejecución a la vez (RF-07) bloquearía las siguientes para siempre.
"""

import logging

from app.db import SessionLocal
from app.services.ejecuciones import marcar_interrumpidas

logger = logging.getLogger(__name__)


def main() -> None:
    with SessionLocal() as db:
        if marcadas := marcar_interrumpidas(db):
            logger.warning("Ejecuciones interrumpidas marcadas como error: %d", marcadas)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    main()
