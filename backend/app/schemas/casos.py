from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from app.models.estados import EstadoCaso, EstadoGeneracion, TipoCaso


class CasoSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    historia_id: int
    generacion_id: int | None
    titulo: str
    tipo: TipoCaso
    gherkin: str
    estado: EstadoCaso
    valido: bool
    errores_validacion: list[str] = Field(
        description="Errores de la validación (RF-04); vacío si el caso es válido."
    )
    creado_en: datetime
    actualizado_en: datetime

    @computed_field
    @property
    def codigo(self) -> str:
        return f"CP-{self.id}"

    @field_validator("errores_validacion", mode="before")
    @classmethod
    def nulo_a_lista(cls, valor: list[str] | None) -> list[str]:
        return valor or []


class GeneracionSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    historia_id: int
    proveedor: str
    modelo: str
    version_prompt: str
    estado: EstadoGeneracion
    duracion_ms: int | None
    mensaje_error: str | None
    creada_en: datetime
    casos: list[CasoSalida] = Field(description="Casos creados por esta generación.")

    @computed_field
    @property
    def casos_validos(self) -> int:
        return sum(caso.valido for caso in self.casos)

    @computed_field
    @property
    def casos_invalidos(self) -> int:
        return sum(not caso.valido for caso in self.casos)
