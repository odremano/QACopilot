"""Tarjeta de un caso de prueba con sus acciones de revisión humana (RF-05).

Las acciones usan callbacks (on_click): se ejecutan antes de volver a dibujar la página, así
el caso ya aparece con su estado nuevo y con el aviso del resultado adentro de su tarjeta.
"""

from collections.abc import Callable

import streamlit as st

from lib import api
from lib.formato import ESTADOS_CASO, etiqueta_caso

AVISO = "aviso_caso"  # (caso_id, nivel, mensaje): se muestra una vez, dentro del caso
MOSTRAR_AVISO = {"ok": st.success, "advertencia": st.warning, "error": st.error}


def _avisar(caso_id: int, nivel: str, mensaje: str) -> None:
    st.session_state[AVISO] = (caso_id, nivel, mensaje)


def _clave_edicion(caso: dict) -> str:
    return f"editando_{caso['id']}"


def _cambiar_estado(caso: dict, accion: Callable[[int], dict]) -> None:
    try:
        actualizado = accion(caso["id"])
    except api.ErrorApi as error:
        _avisar(caso["id"], "error", error.mensaje)
        return
    estado = ESTADOS_CASO[actualizado["estado"]].lower()
    _avisar(caso["id"], "ok", f"{actualizado['codigo']} quedó {estado}.")


def _guardar_edicion(caso: dict, clave_texto: str) -> None:
    try:
        actualizado = api.editar_caso(caso["id"], st.session_state[clave_texto])
    except api.ErrorApi as error:
        _avisar(caso["id"], "error", error.mensaje)
        return
    st.session_state[_clave_edicion(caso)] = False
    if actualizado["valido"]:
        _avisar(caso["id"], "ok", f"Se guardó {caso['codigo']} y es válido: ya podés aprobarlo.")
    else:
        _avisar(
            caso["id"],
            "advertencia",
            f"Se guardó {caso['codigo']}, pero sigue inválido: revisá los errores.",
        )


def _poner_edicion(caso: dict, activa: bool) -> None:
    st.session_state[_clave_edicion(caso)] = activa


def _errores(caso: dict) -> None:
    if caso["errores_validacion"]:
        st.error(
            "**El caso no es válido:**\n"
            + "\n".join(f"- {error}" for error in caso["errores_validacion"])
        )


def _formulario_edicion(caso: dict) -> None:
    # La clave incluye la fecha de actualización: tras guardar, el texto se recarga.
    clave_texto = f"gherkin_{caso['id']}_{caso['actualizado_en']}"
    lineas = caso["gherkin"].count("\n") + 2
    st.text_area(
        "Gherkin",
        value=caso["gherkin"],
        key=clave_texto,
        height=max(160, 26 * lineas),
        help=(
            "Una línea «Escenario:» y un paso por línea. Cada paso empieza con Dado, Cuando, "
            "Entonces, Y o Pero y debe coincidir con un patrón del catálogo."
        ),
    )
    _errores(caso)
    guardar, cancelar, _ = st.columns([1, 1, 3])
    guardar.button(
        "Guardar y revalidar",
        key=f"guardar_{caso['id']}",
        type="primary",
        on_click=_guardar_edicion,
        args=(caso, clave_texto),
    )
    cancelar.button(
        "Cancelar", key=f"cancelar_{caso['id']}", on_click=_poner_edicion, args=(caso, False)
    )


def _acciones(caso: dict) -> None:
    if caso["estado"] != "pendiente":
        columna, ayuda = st.columns([1, 3])
        columna.button(
            "Volver a pendiente",
            key=f"pendiente_{caso['id']}",
            on_click=_cambiar_estado,
            args=(caso, api.volver_a_pendiente),
        )
        ayuda.caption("Para editarlo, primero volvelo a pendiente.")
        return

    aprobar, descartar, editar, _ = st.columns([1, 1, 1, 2])
    aprobar.button(
        "Aprobar",
        key=f"aprobar_{caso['id']}",
        type="primary",
        disabled=not caso["valido"],
        help=None if caso["valido"] else "Solo se aprueban casos válidos: editalo y corregilo.",
        on_click=_cambiar_estado,
        args=(caso, api.aprobar_caso),
    )
    descartar.button(
        "Descartar",
        key=f"descartar_{caso['id']}",
        on_click=_cambiar_estado,
        args=(caso, api.descartar_caso),
    )
    editar.button("Editar", key=f"editar_{caso['id']}", on_click=_poner_edicion, args=(caso, True))


def mostrar_caso(caso: dict) -> None:
    aviso = st.session_state.get(AVISO)
    if aviso and aviso[0] == caso["id"]:
        del st.session_state[AVISO]
    else:
        aviso = None
    editando = caso["estado"] == "pendiente" and st.session_state.get(_clave_edicion(caso), False)

    expandido = bool(aviso) or editando or not caso["valido"]
    with st.expander(etiqueta_caso(caso), expanded=expandido):
        if aviso:
            _, nivel, mensaje = aviso
            MOSTRAR_AVISO[nivel](mensaje)
        if editando:
            _formulario_edicion(caso)
            return
        st.code(caso["gherkin"], language="gherkin")
        _errores(caso)
        _acciones(caso)
