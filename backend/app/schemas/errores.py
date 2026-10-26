from pydantic import BaseModel


class ErrorDetalle(BaseModel):
    detalle: str
