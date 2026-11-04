from pydantic import BaseModel, ConfigDict


class PasoSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    grupo: str
    patron: str
    plantilla: str


class CatalogoSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sut: str
    base_url: str
    version: int
    pasos: list[PasoSalida]
