from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Identity, String, Text, false, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.estados import EstadoCaso, TipoCaso, check_valores

if TYPE_CHECKING:
    from app.models.generacion import Generacion
    from app.models.historia_usuario import HistoriaUsuario
    from app.models.resultado_caso import ResultadoCaso


class CasoPrueba(Base):
    __tablename__ = "caso_prueba"
    __table_args__ = (
        check_valores("tipo", TipoCaso),
        check_valores("estado", EstadoCaso),
    )

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    historia_id: Mapped[int] = mapped_column(
        ForeignKey("historia_usuario.id", ondelete="CASCADE"), index=True
    )
    # Nullable: si se borra una generación, el caso (por ejemplo, aprobado) se conserva.
    generacion_id: Mapped[int | None] = mapped_column(
        ForeignKey("generacion.id", ondelete="SET NULL"), index=True
    )
    titulo: Mapped[str] = mapped_column(String(200))
    tipo: Mapped[str] = mapped_column(String(20))
    gherkin: Mapped[str] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(
        String(20), default=EstadoCaso.PENDIENTE, server_default=EstadoCaso.PENDIENTE.value
    )
    valido: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    errores_validacion: Mapped[Any | None] = mapped_column(JSONB)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    historia: Mapped[HistoriaUsuario] = relationship(back_populates="casos")
    generacion: Mapped[Generacion | None] = relationship(back_populates="casos")
    resultados: Mapped[list[ResultadoCaso]] = relationship(
        back_populates="caso", cascade="all, delete-orphan", passive_deletes=True
    )

    @property
    def codigo(self) -> str:
        return f"CP-{self.id}"
