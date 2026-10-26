from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Identity, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.caso_prueba import CasoPrueba
    from app.models.ejecucion import Ejecucion
    from app.models.generacion import Generacion


class HistoriaUsuario(Base):
    __tablename__ = "historia_usuario"

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    titulo: Mapped[str] = mapped_column(String(120))
    descripcion: Mapped[str] = mapped_column(Text)
    criterios_aceptacion: Mapped[str | None] = mapped_column(Text)
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    actualizada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    generaciones: Mapped[list[Generacion]] = relationship(
        back_populates="historia", cascade="all, delete-orphan", passive_deletes=True
    )
    casos: Mapped[list[CasoPrueba]] = relationship(
        back_populates="historia", cascade="all, delete-orphan", passive_deletes=True
    )
    ejecuciones: Mapped[list[Ejecucion]] = relationship(
        back_populates="historia", cascade="all, delete-orphan", passive_deletes=True
    )

    @property
    def codigo(self) -> str:
        return f"HU-{self.id}"
