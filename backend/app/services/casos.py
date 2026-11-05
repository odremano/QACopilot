"""Casos de prueba de una historia (RF-05)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import NoEncontrado
from app.models import CasoPrueba, HistoriaUsuario
from app.schemas.casos import CasoSalida


def listar_casos(db: Session, historia_id: int) -> list[CasoSalida]:
    if db.get(HistoriaUsuario, historia_id) is None:
        raise NoEncontrado(f"La historia HU-{historia_id} no existe")
    casos = db.scalars(
        select(CasoPrueba).where(CasoPrueba.historia_id == historia_id).order_by(CasoPrueba.id)
    )
    return [CasoSalida.model_validate(caso) for caso in casos]
