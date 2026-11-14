from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from app.models.estados import EstadoCaso, EstadoGeneracion, TipoCaso


class CasoEdicion(BaseModel):
    gherkin: str = Field(
        min_length=1,
        description="Escenario completo: línea «Escenario:» y un paso del catálogo por línea.",
    )

    @field_validator("gherkin")
    @classmethod
    def no_vacio(cls, valor: str) -> str:
        if not valor.strip():
            raise ValueError("el Gherkin no puede estar vacío")
        return valor


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


class GeneracionResumen(BaseModel):
    """Ítem del historial de generaciones (RF-12)."""

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
    casos_validos: int | None = Field(
        description="Casos válidos al momento de generar; nulo en generaciones anteriores a S6."
    )
    casos_invalidos: int | None = Field(
        description="Casos inválidos al momento de generar; nulo en generaciones anteriores a S6."
    )


class GeneracionSalida(GeneracionResumen):
    casos: list[CasoSalida] = Field(description="Casos creados por esta generación.")
