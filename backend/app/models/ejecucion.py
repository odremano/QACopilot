from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Identity, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.estados import EstadoEjecucion, check_valores

if TYPE_CHECKING:
    from app.models.historia_usuario import HistoriaUsuario
    from app.models.resultado_caso import ResultadoCaso


class Ejecucion(Base):
    __tablename__ = "ejecucion"
    __table_args__ = (check_valores("estado", EstadoEjecucion),)

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    historia_id: Mapped[int] = mapped_column(
        ForeignKey("historia_usuario.id", ondelete="CASCADE"), index=True
    )
    estado: Mapped[str] = mapped_column(
        String(20),
        default=EstadoEjecucion.EN_CURSO,
        server_default=EstadoEjecucion.EN_CURSO.value,
    )
    iniciada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    finalizada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    total: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    aprobados: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    fallidos: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    omitidos: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    log: Mapped[str | None] = mapped_column(Text)

    historia: Mapped[HistoriaUsuario] = relationship(back_populates="ejecuciones")
    resultados: Mapped[list[ResultadoCaso]] = relationship(
        back_populates="ejecucion", cascade="all, delete-orphan", passive_deletes=True
    )
