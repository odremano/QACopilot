"""Modelo de datos (spec, sección 8). Importar este paquete registra todas las tablas."""

from app.models.caso_prueba import CasoPrueba
from app.models.ejecucion import Ejecucion
from app.models.generacion import Generacion
from app.models.historia_usuario import HistoriaUsuario
from app.models.resultado_caso import ResultadoCaso

__all__ = ["CasoPrueba", "Ejecucion", "Generacion", "HistoriaUsuario", "ResultadoCaso"]
