from datetime import datetime
from zoneinfo import ZoneInfo

ZONA_HORARIA = ZoneInfo("America/Argentina/Buenos_Aires")


def fecha(iso: str | None) -> str:
    """Convierte una fecha ISO (UTC) del backend a 'dd/mm/aaaa HH:MM' en hora argentina."""
    if not iso:
        return "—"
    return datetime.fromisoformat(iso).astimezone(ZONA_HORARIA).strftime("%d/%m/%Y %H:%M")


def etiqueta_historia(historia: dict) -> str:
    return f"{historia['codigo']} · {historia['titulo']}"


TIPOS_CASO = {"positivo": "Positivo", "negativo": "Negativo", "limite": "Límite"}
ESTADOS_CASO = {"pendiente": "Pendiente", "aprobado": "Aprobado", "descartado": "Descartado"}


def etiqueta_caso(caso: dict) -> str:
    icono = "✅" if caso["valido"] else "⚠️"
    tipo = TIPOS_CASO.get(caso["tipo"], caso["tipo"])
    estado = ESTADOS_CASO.get(caso["estado"], caso["estado"])
    return f"{icono} {caso['codigo']} · {caso['titulo']} — {tipo} · {estado}"
