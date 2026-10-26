import streamlit as st

from lib import api
from lib.formato import etiqueta_historia, fecha

st.set_page_config(page_title="QA Copilot", layout="wide")

st.title("Detalle de historia")

try:
    historias = api.listar_historias()
except api.ErrorApi as error:
    st.error(error.mensaje)
    st.stop()

if not historias:
    st.info("Todavía no hay historias cargadas.")
    st.stop()

# La historia llega por ?id=3; si no hay id (o no existe), se elige con el selector.
ids = [h["id"] for h in historias]
id_pedido = st.query_params.get("id")
indice = None
if id_pedido is not None:
    if id_pedido.isdigit() and int(id_pedido) in ids:
        indice = ids.index(int(id_pedido))
    else:
        st.warning(f"La historia HU-{id_pedido} no existe. Elegí otra del listado.")

elegida = st.selectbox(
    "Historia",
    historias,
    index=indice,
    format_func=etiqueta_historia,
    placeholder="Elegí una historia",
)
if elegida is None:
    st.stop()
st.query_params["id"] = str(elegida["id"])

try:
    historia = api.obtener_historia(elegida["id"])
except api.ErrorApi as error:
    st.error(error.mensaje)
    st.stop()

if mensaje := st.session_state.pop("historia_editada", None):
    st.success(mensaje)

st.header(etiqueta_historia(historia))
st.caption(
    f"Creada: {fecha(historia['creada_en'])} · Actualizada: {fecha(historia['actualizada_en'])}"
)

datos, casos = st.columns([3, 2])
with datos:
    st.markdown("**Descripción**")
    st.write(historia["descripcion"])
    st.markdown("**Criterios de aceptación**")
    if historia["criterios_aceptacion"]:
        st.markdown(historia["criterios_aceptacion"])
    else:
        st.caption("Sin criterios cargados.")
with casos:
    resumen = historia["resumen_casos"]
    fila1 = st.columns(2)
    fila1[0].metric("Pendientes", resumen["pendiente"])
    fila1[1].metric("Aprobados", resumen["aprobado"])
    fila2 = st.columns(2)
    fila2[0].metric("Descartados", resumen["descartado"])
    fila2[1].metric("Inválidos", resumen["invalidos"])

# La clave incluye la fecha de actualización: tras guardar, el formulario se recarga prellenado.
with (
    st.expander("Editar historia"),
    st.form(f"editar_{historia['id']}_{historia['actualizada_en']}"),
):
    titulo = st.text_input("Título", value=historia["titulo"], max_chars=api.TITULO_MAX)
    descripcion = st.text_area("Descripción", value=historia["descripcion"], height=100)
    criterios = st.text_area(
        "Criterios de aceptación (opcional)",
        value=historia["criterios_aceptacion"] or "",
        height=120,
    )
    guardar = st.form_submit_button("Guardar cambios", type="primary")

if guardar:
    cambios = {"titulo": titulo, "descripcion": descripcion, "criterios_aceptacion": criterios}
    try:
        editada = api.editar_historia(historia["id"], cambios)
    except api.ErrorApi as error:
        st.error(error.mensaje)
    else:
        st.session_state["historia_editada"] = f"Se guardaron los cambios de {editada['codigo']}."
        st.rerun()

st.divider()
PROXIMAMENTE = [
    ("Generar casos", "Generar casos con IA", "S4"),
    ("Casos de prueba", "Revisar casos", "S4"),
    ("Exportar", "Descargar .spec.ts", "S5"),
    ("Ejecutar", "Ejecutar pruebas", "S5"),
]
for columna, (seccion, boton, semana) in zip(st.columns(4), PROXIMAMENTE, strict=True):
    with columna:
        st.subheader(seccion)
        st.button(boton, disabled=True, key=f"btn_{seccion}")
        st.caption(f"Próximamente ({semana})")
