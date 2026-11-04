import streamlit as st

from lib import api

st.set_page_config(page_title="QA Copilot", layout="wide")

st.title("Catálogo de pasos")
st.write(
    "Pasos Gherkin permitidos para el sistema bajo prueba, agrupados por funcionalidad "
    "(solo lectura). Cada paso de un caso debe coincidir con uno de estos patrones; "
    'los valores van entre comillas en lugar de `"{texto}"`. El código de Playwright sale de '
    "la plantilla del paso, nunca del LLM."
)

try:
    catalogo = api.obtener_catalogo()
except api.ErrorApi as error:
    st.error(error.mensaje)
    st.stop()

pasos = catalogo["pasos"]
grupos: dict[str, list[dict]] = {}
for paso in pasos:
    grupos.setdefault(paso["grupo"], []).append(paso)

columnas = st.columns(4)
columnas[0].metric("Sistema bajo prueba", catalogo["sut"])
columnas[1].metric("Versión del catálogo", catalogo["version"])
columnas[2].metric("Pasos", len(pasos))
columnas[3].metric("Grupos", len(grupos))
st.caption(f"URL base: {catalogo['base_url']}")

for grupo, pasos_grupo in grupos.items():
    with st.expander(f"{grupo.capitalize()} ({len(pasos_grupo)})", expanded=True):
        for paso in pasos_grupo:
            st.markdown(f"**{paso['patron']}**  \n`{paso['id']}`")
            st.code(paso["plantilla"], language="typescript")
