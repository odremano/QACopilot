import streamlit as st

from lib import api, rutas
from lib.formato import fecha

st.set_page_config(page_title="QA Copilot", layout="wide")

st.title("Historias de usuario")

# El formulario se limpia tras un alta exitosa cambiando su clave (widgets nuevos y vacíos).
st.session_state.setdefault("alta_version", 0)
if creada := st.session_state.pop("historia_creada", None):
    st.success(f"Se creó la historia {creada['codigo']}.")
    st.page_link(
        rutas.DETALLE, label=f"Abrir {creada['codigo']}", query_params={"id": creada["id"]}
    )

try:
    historias = api.listar_historias()
except api.ErrorApi as error:
    st.error(error.mensaje)
    st.stop()

st.subheader("Listado")
if historias:
    filas = [
        {
            "Código": h["codigo"],
            "Título": h["titulo"],
            "Pendientes": h["resumen_casos"]["pendiente"],
            "Aprobados": h["resumen_casos"]["aprobado"],
            "Descartados": h["resumen_casos"]["descartado"],
            "Inválidos": h["resumen_casos"]["invalidos"],
            "Actualizada": fecha(h["actualizada_en"]),
        }
        for h in historias
    ]
    seleccion = st.dataframe(
        filas,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="tabla_historias",
    )
    st.caption("Seleccioná una fila para abrir el detalle de la historia.")
    if seleccion.selection.rows:
        elegida = historias[seleccion.selection.rows[0]]
        st.page_link(
            rutas.DETALLE,
            label=f"Abrir detalle de {elegida['codigo']}",
            query_params={"id": elegida["id"]},
        )
else:
    st.info("Todavía no hay historias cargadas.")

st.subheader("Nueva historia")
version = st.session_state["alta_version"]
with st.form(f"alta_historia_{version}"):
    titulo = st.text_input("Título", max_chars=api.TITULO_MAX)
    descripcion = st.text_area("Descripción", placeholder="Como … quiero … para …", height=100)
    criterios = st.text_area(
        "Criterios de aceptación (opcional)",
        placeholder="- Un criterio por línea",
        height=120,
    )
    guardar = st.form_submit_button("Guardar historia", type="primary")

if guardar:
    datos = {"titulo": titulo, "descripcion": descripcion, "criterios_aceptacion": criterios}
    try:
        historia = api.crear_historia(datos)
    except api.ErrorApi as error:
        st.error(error.mensaje)
    else:
        st.session_state["historia_creada"] = historia
        st.session_state["alta_version"] = version + 1
        st.rerun()
