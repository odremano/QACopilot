import streamlit as st

from lib import api

st.set_page_config(page_title="QA Copilot", layout="wide")

st.title("Acerca de QA Copilot")
st.markdown(
    """
QA Copilot genera casos de prueba Gherkin en español a partir de historias de usuario,
los valida contra un catálogo de pasos, permite revisarlos y aprobarlos, los exporta a
scripts de Playwright (TypeScript) generados por plantillas y los ejecuta contra SauceDemo.

**Principio rector:** la IA propone, el sistema valida y la persona decide.
El LLM nunca escribe código ejecutable.

Proyecto final de Prácticas de Laboratorio · Universidad de Belgrano · 2026.
"""
)

st.subheader("Estado del servicio")
try:
    salud = api.salud()
except api.ErrorApi as error:
    st.error(error.mensaje)
else:
    llm = salud["llm"]
    columnas = st.columns(4)
    columnas[0].metric("API", "OK" if salud["estado"] == "ok" else "Degradada")
    columnas[1].metric("Base de datos", "OK" if salud["base_de_datos"] == "ok" else "Error")
    columnas[2].metric("Proveedor de LLM", llm["proveedor"])
    columnas[3].metric("Versión", salud["version"])
    st.write(f"**Modelo configurado:** {llm['modelo']}")
    if llm["configurado"]:
        st.success("El proveedor de LLM está configurado.")
    else:
        st.warning("El proveedor de LLM todavía no está configurado (se usa a partir de S4).")

st.subheader("Documentación de la API")
st.markdown(f"[Abrir la documentación OpenAPI]({api.API_PUBLIC_URL}/docs)")
