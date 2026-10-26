from datetime import datetime
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    computed_field,
    field_validator,
)

Titulo = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
TextoObligatorio = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class HistoriaEntrada(BaseModel):
    """Datos para crear o editar una historia (mismas reglas en alta y edición)."""

    titulo: Titulo = Field(description="Obligatorio, hasta 120 caracteres.")
    descripcion: TextoObligatorio = Field(
        description="Obligatoria. Se sugiere el formato «Como… quiero… para…»."
    )
    criterios_aceptacion: str | None = Field(
        default=None, description="Opcional. Si llega vacío se guarda como nulo."
    )

    @field_validator("criterios_aceptacion")
    @classmethod
    def vacio_a_nulo(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        return valor.strip() or None


class ResumenCasos(BaseModel):
    pendiente: int = 0
    aprobado: int = 0
    descartado: int = 0
    invalidos: int = 0


class HistoriaBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    creada_en: datetime
    actualizada_en: datetime
    resumen_casos: ResumenCasos = ResumenCasos()

    @computed_field
    @property
    def codigo(self) -> str:
        return f"HU-{self.id}"


class HistoriaResumen(HistoriaBase):
    """Ítem del listado."""


class HistoriaDetalle(HistoriaBase):
    descripcion: str
    criterios_aceptacion: str | None
