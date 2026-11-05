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


ESTADOS_EJECUCION = {"en_curso": "⏳ En curso", "finalizada": "Finalizada", "error": "❌ Error"}
ESTADOS_RESULTADO = {"aprobado": "✅ Aprobado", "fallido": "❌ Fallido", "omitido": "⏭️ Omitido"}


def segundos(ms: int | float | None) -> str:
    """Duración legible: '850 ms', '5,9 s' o '1 min 12 s'."""
    if ms is None:
        return "—"
    if ms < 1000:
        return f"{round(ms)} ms"
    if ms < 60_000:
        return f"{ms / 1000:.1f} s".replace(".", ",")
    minutos, resto = divmod(round(ms / 1000), 60)
    return f"{minutos} min {resto} s"


def duracion_ejecucion(ejecucion: dict) -> str:
    if not ejecucion["finalizada_en"]:
        return "—"
    inicio = datetime.fromisoformat(ejecucion["iniciada_en"])
    fin = datetime.fromisoformat(ejecucion["finalizada_en"])
    return segundos((fin - inicio).total_seconds() * 1000)


def porcentaje(valor: float | None) -> str:
    return "—" if valor is None else f"{valor:g} %".replace(".", ",")


def etiqueta_ejecucion(ejecucion: dict) -> str:
    estado = ESTADOS_EJECUCION.get(ejecucion["estado"], ejecucion["estado"])
    historia = ejecucion["historia"]
    return (
        f"Ejecución {ejecucion['id']} · {historia['codigo']} {historia['titulo']} · {estado} · "
        f"{fecha(ejecucion['iniciada_en'])}"
    )


def etiqueta_resultado(resultado: dict) -> str:
    estado = ESTADOS_RESULTADO.get(resultado["estado"], resultado["estado"])
    caso = resultado["caso"]
    return f"{caso['codigo']} · {caso['titulo']} — {estado} · {segundos(resultado['duracion_ms'])}"
