from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Identity, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.estados import EstadoGeneracion, check_valores

if TYPE_CHECKING:
    from app.models.caso_prueba import CasoPrueba
    from app.models.historia_usuario import HistoriaUsuario


class Generacion(Base):
    __tablename__ = "generacion"
    __table_args__ = (check_valores("estado", EstadoGeneracion),)

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    historia_id: Mapped[int] = mapped_column(
        ForeignKey("historia_usuario.id", ondelete="CASCADE"), index=True
    )
    proveedor: Mapped[str] = mapped_column(String(50))
    modelo: Mapped[str] = mapped_column(String(100))
    version_prompt: Mapped[str] = mapped_column(String(20))
    estado: Mapped[str] = mapped_column(String(20))
    duracion_ms: Mapped[int | None] = mapped_column(Integer)
    respuesta_cruda: Mapped[Any | None] = mapped_column(JSONB)
    mensaje_error: Mapped[str | None] = mapped_column(Text)
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    historia: Mapped[HistoriaUsuario] = relationship(back_populates="generaciones")
    casos: Mapped[list[CasoPrueba]] = relationship(back_populates="generacion")
