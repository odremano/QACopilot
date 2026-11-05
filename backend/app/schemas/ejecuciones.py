from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.models.estados import EstadoEjecucion, EstadoResultado


class HistoriaReferencia(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    titulo: str


class CasoReferencia(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    titulo: str


class EjecucionSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    historia: HistoriaReferencia
    estado: EstadoEjecucion
    iniciada_en: datetime
    finalizada_en: datetime | None
    total: int = Field(description="Casos aprobados que se ejecutan.")
    aprobados: int
    fallidos: int
    omitidos: int

    @computed_field(description="Porcentaje de casos aprobados; nulo hasta que finaliza.")
    @property
    def porcentaje_exito(self) -> float | None:
        if self.estado != EstadoEjecucion.FINALIZADA or not self.total:
            return None
        return round(self.aprobados * 100 / self.total, 1)


class ResultadoSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    caso: CasoReferencia
    estado: EstadoResultado
    duracion_ms: int | None
    mensaje_error: str | None
    ruta_captura: str | None = Field(exclude=True)

    @computed_field(description="Ruta de la API para descargar la captura del fallo (RF-08).")
    @property
    def url_captura(self) -> str | None:
        return f"/evidencias/{self.id}" if self.ruta_captura else None


class EjecucionDetalle(EjecucionSalida):
    log: str | None = Field(description="Salida de Playwright o motivo del error.")
    resultados: list[ResultadoSalida]
