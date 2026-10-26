from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Identity, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.estados import EstadoResultado, check_valores

if TYPE_CHECKING:
    from app.models.caso_prueba import CasoPrueba
    from app.models.ejecucion import Ejecucion


class ResultadoCaso(Base):
    __tablename__ = "resultado_caso"
    __table_args__ = (check_valores("estado", EstadoResultado),)

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    ejecucion_id: Mapped[int] = mapped_column(
        ForeignKey("ejecucion.id", ondelete="CASCADE"), index=True
    )
    caso_id: Mapped[int] = mapped_column(
        ForeignKey("caso_prueba.id", ondelete="CASCADE"), index=True
    )
    estado: Mapped[str] = mapped_column(String(20))
    duracion_ms: Mapped[int | None] = mapped_column(Integer)
    mensaje_error: Mapped[str | None] = mapped_column(Text)
    ruta_captura: Mapped[str | None] = mapped_column(String(500))

    ejecucion: Mapped[Ejecucion] = relationship(back_populates="resultados")
    caso: Mapped[CasoPrueba] = relationship(back_populates="resultados")
