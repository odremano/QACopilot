import streamlit as st

from lib import api, rutas
from lib.formato import (
    ESTADOS_EJECUCION,
    duracion_ejecucion,
    fecha,
    porcentaje,
    resultado_ejecucion,
)

ULTIMAS_EJECUCIONES = 10

st.set_page_config(page_title="QA Copilot", layout="wide")

st.title("QA Copilot")
st.caption("La IA propone, el sistema valida y la persona decide.")

try:
    historias = api.listar_historias()
    ejecuciones = api.listar_ejecuciones()
except api.ErrorApi as error:
    st.error(error.mensaje)
    st.stop()

totales = {"pendiente": 0, "aprobado": 0, "descartado": 0, "invalidos": 0}
for historia in historias:
    for estado in totales:
        totales[estado] += historia["resumen_casos"][estado]

columnas = st.columns(6)
columnas[0].metric("Historias", len(historias))
columnas[1].metric("Casos pendientes", totales["pendiente"])
columnas[2].metric("Casos aprobados", totales["aprobado"])
columnas[3].metric("Casos descartados", totales["descartado"])
columnas[4].metric("Casos inválidos", totales["invalidos"])
columnas[5].metric("Ejecuciones", len(ejecuciones))

# --- Por historia: casos por estado y última ejecución (CA-09) ---------------

st.subheader("Historias")
if not historias:
    st.info("Todavía no hay historias cargadas.")
else:
    filas = []
    for h in historias:
        ultima = h["ultima_ejecucion"]
        filas.append(
            {
                "Código": h["codigo"],
                "Título": h["titulo"],
                "Pendientes": h["resumen_casos"]["pendiente"],
                "Aprobados": h["resumen_casos"]["aprobado"],
                "Descartados": h["resumen_casos"]["descartado"],
                "Inválidos": h["resumen_casos"]["invalidos"],
                "Última ejecución": fecha(ultima["iniciada_en"]) if ultima else "Sin ejecutar",
                "Resultado": resultado_ejecucion(ultima) if ultima else "—",
            }
        )
    seleccion = st.dataframe(
        filas,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="panel_historias",
    )
    st.caption("Seleccioná una historia para abrir su detalle o su última ejecución.")
    if seleccion.selection.rows:
        elegida = historias[seleccion.selection.rows[0]]
        izquierda, derecha = st.columns(2)
        izquierda.page_link(
            rutas.DETALLE,
            label=f"Abrir detalle de {elegida['codigo']}",
            query_params={"id": elegida["id"]},
        )
        if ultima := elegida["ultima_ejecucion"]:
            derecha.page_link(
                rutas.EJECUCIONES,
                label=f"Ver ejecución {ultima['id']}",
                query_params={"id": ultima["id"]},
            )

# --- Por ejecución: aprobados, fallidos y porcentaje de éxito (CA-09) ---------

st.subheader("Últimas ejecuciones")
if not ejecuciones:
    st.info("Todavía no hay ejecuciones.")
else:
    recientes = ejecuciones[:ULTIMAS_EJECUCIONES]
    seleccion = st.dataframe(
        [
            {
                "Ejecución": e["id"],
                "Historia": f"{e['historia']['codigo']} · {e['historia']['titulo']}",
                "Estado": ESTADOS_EJECUCION.get(e["estado"], e["estado"]),
                "Inicio": fecha(e["iniciada_en"]),
                "Duración": duracion_ejecucion(e),
                "Casos": e["total"],
                "Aprobados": e["aprobados"],
                "Fallidos": e["fallidos"],
                "Omitidos": e["omitidos"],
                "Éxito": porcentaje(e["porcentaje_exito"]),
            }
            for e in recientes
        ],
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="panel_ejecuciones",
    )
    if seleccion.selection.rows:
        elegida = recientes[seleccion.selection.rows[0]]
        st.page_link(
            rutas.EJECUCIONES,
            label=f"Ver el detalle de la ejecución {elegida['id']}",
            query_params={"id": elegida["id"]},
        )
    else:
        st.caption("Seleccioná una ejecución para ver el resultado de cada caso y sus capturas.")
    if len(ejecuciones) > ULTIMAS_EJECUCIONES:
        st.page_link(rutas.EJECUCIONES, label="Ver todas las ejecuciones")
