import streamlit as st

from lib import api, marca

marca.configurar_pagina()

st.title(f"Acerca de {marca.NOMBRE_APP}")
st.markdown(
    """
Casewright genera casos de prueba Gherkin en español a partir de historias de usuario,
los valida contra un catálogo de pasos, permite revisarlos y aprobarlos, los exporta a
scripts de Playwright (TypeScript) generados por plantillas y los ejecuta contra SauceDemo.

**Principio rector:** la IA propone, el sistema valida y la persona decide.
El LLM nunca escribe código ejecutable.

**El nombre:** *Case* (caso de prueba) + *-wright* (sufijo inglés de oficio, como en
*playwright* o *shipwright*): el que construye casos de prueba, con un guiño a Playwright,
la herramienta con la que se ejecutan.

Proyecto final de Prácticas de Laboratorio · Universidad de Belgrano · 2026.
Durante el desarrollo se llamó QA Copilot, nombre con el que figura en la especificación.
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
