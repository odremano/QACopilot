"""Historias de ejemplo sobre SauceDemo (RF-01). Idempotente: si ya hay historias, no hace nada."""

import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import HistoriaUsuario

logger = logging.getLogger(__name__)

HISTORIAS_EJEMPLO = [
    {
        "titulo": "Inicio de sesión",
        "descripcion": (
            "Como cliente de Swag Labs quiero iniciar sesión con mi usuario y contraseña "
            "para acceder al catálogo de productos."
        ),
        "criterios_aceptacion": (
            "- Con un usuario válido (standard_user / secret_sauce) ingreso y veo el listado "
            "de productos.\n"
            "- Con el usuario bloqueado (locked_out_user) el ingreso se rechaza y veo un mensaje "
            "que indica que el usuario está bloqueado.\n"
            "- Con credenciales inválidas el ingreso se rechaza y veo un mensaje de que el "
            "usuario y la contraseña no coinciden.\n"
            "- Si dejo vacío el usuario o la contraseña, veo un mensaje que indica que el campo "
            "es obligatorio."
        ),
    },
    {
        "titulo": "Carrito de compras",
        "descripcion": (
            "Como cliente de Swag Labs quiero agregar y quitar productos del carrito "
            "para preparar mi compra."
        ),
        "criterios_aceptacion": (
            "- Desde el inventario puedo agregar productos al carrito.\n"
            "- El contador del ícono del carrito refleja la cantidad de productos agregados.\n"
            "- Puedo quitar productos desde el inventario o desde el carrito, y el contador "
            "se actualiza.\n"
            "- El carrito conserva los productos al navegar entre el inventario, el detalle "
            "de un producto y el carrito."
        ),
    },
    {
        "titulo": "Checkout",
        "descripcion": (
            "Como cliente de Swag Labs quiero completar el checkout de los productos de mi "
            "carrito para finalizar la compra."
        ),
        "criterios_aceptacion": (
            "- Debo completar nombre, apellido y código postal; si falta alguno, veo un mensaje "
            "que indica el campo obligatorio.\n"
            "- Con los datos completos veo el resumen de la compra con los productos, el "
            "subtotal, los impuestos y el total.\n"
            "- Al finalizar la compra veo la confirmación del pedido.\n"
            "- Si cancelo en el paso de datos personales, vuelvo al carrito."
        ),
    },
]


def cargar_ejemplos(db: Session) -> int:
    """Inserta las historias de ejemplo si la tabla está vacía. Devuelve cuántas insertó."""
    if db.scalar(select(func.count()).select_from(HistoriaUsuario)):
        return 0
    db.add_all(HistoriaUsuario(**datos) for datos in HISTORIAS_EJEMPLO)
    db.commit()
    return len(HISTORIAS_EJEMPLO)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    with SessionLocal() as db:
        insertadas = cargar_ejemplos(db)
    if insertadas:
        logger.info("Se cargaron %d historias de ejemplo.", insertadas)
    else:
        logger.info("Ya hay historias cargadas; no se agregan ejemplos.")


if __name__ == "__main__":
    main()
