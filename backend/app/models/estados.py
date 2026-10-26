"""Valores válidos de los estados. Única fuente de verdad para constraints y schemas."""

from enum import StrEnum

from sqlalchemy import CheckConstraint


class EstadoGeneracion(StrEnum):
    OK = "ok"
    ERROR = "error"


class TipoCaso(StrEnum):
    POSITIVO = "positivo"
    NEGATIVO = "negativo"
    LIMITE = "limite"


class EstadoCaso(StrEnum):
    PENDIENTE = "pendiente"
    APROBADO = "aprobado"
    DESCARTADO = "descartado"


class EstadoEjecucion(StrEnum):
    EN_CURSO = "en_curso"
    FINALIZADA = "finalizada"
    ERROR = "error"


class EstadoResultado(StrEnum):
    APROBADO = "aprobado"
    FALLIDO = "fallido"
    OMITIDO = "omitido"


def check_valores(columna: str, valores: type[StrEnum]) -> CheckConstraint:
    """CheckConstraint `columna IN (...)` con nombre estable (ck_<tabla>_<columna>_valido)."""
    lista = ", ".join(f"'{v.value}'" for v in valores)
    return CheckConstraint(f"{columna} IN ({lista})", name=f"{columna}_valido")
