"""Prompt versionado para la generación de casos (RF-03, Anexo A).

La plantilla vive en `prompts/<versión>.md` y su versión se guarda en cada generación. Los
marcadores se reemplazan con str.replace: los patrones del catálogo contienen llaves.
"""

import json
from functools import cache

from app.catalogo import RAIZ_BACKEND, Catalogo
from app.models import HistoriaUsuario

VERSION_PROMPT = "v1"
RUTA_PROMPTS = RAIZ_BACKEND / "prompts"

# Anexo B: ejemplo de salida que el modelo debe imitar.
EJEMPLO_SALIDA = {
    "casos": [
        {
            "titulo": "Ingreso exitoso con usuario estándar",
            "tipo": "positivo",
            "pasos": [
                "Dado que estoy en la página de inicio de sesión",
                'Cuando ingreso el usuario "standard_user"',
                'Y ingreso la contraseña "secret_sauce"',
                "Y presiono el botón de ingresar",
                "Entonces veo el listado de productos",
            ],
        },
        {
            "titulo": "Ingreso rechazado para usuario bloqueado",
            "tipo": "negativo",
            "pasos": [
                "Dado que estoy en la página de inicio de sesión",
                'Cuando ingreso el usuario "locked_out_user"',
                'Y ingreso la contraseña "secret_sauce"',
                "Y presiono el botón de ingresar",
                'Entonces veo el mensaje de error "Epic sadface: Sorry, this user has been '
                'locked out."',
            ],
        },
    ]
}


@cache
def _plantilla(version: str) -> str:
    return (RUTA_PROMPTS / f"{version}.md").read_text(encoding="utf-8")


def _listar_catalogo(catalogo: Catalogo) -> str:
    grupos: dict[str, list[str]] = {}
    for paso in catalogo.pasos:
        grupos.setdefault(paso.grupo, []).append(paso.patron)
    return "\n".join(
        f"[{grupo}]\n" + "\n".join(f"- {patron}" for patron in patrones)
        for grupo, patrones in grupos.items()
    )


def mensaje_sistema(catalogo: Catalogo) -> str:
    return (
        _plantilla(VERSION_PROMPT)
        .replace("<<SUT>>", catalogo.sut)
        .replace("<<CATALOGO>>", _listar_catalogo(catalogo))
        .replace("<<CONTEXTO>>", catalogo.contexto.strip() or "(sin datos adicionales)")
        .replace("<<EJEMPLO>>", json.dumps(EJEMPLO_SALIDA, ensure_ascii=False, indent=2))
        .strip()
    )


def mensaje_usuario(historia: HistoriaUsuario) -> str:
    criterios = historia.criterios_aceptacion or "(sin criterios de aceptación cargados)"
    return (
        f"Historia de usuario: {historia.titulo}\n\n"
        f"Descripción:\n{historia.descripcion}\n\n"
        f"Criterios de aceptación:\n{criterios}"
    )


def armar_mensajes(historia: HistoriaUsuario, catalogo: Catalogo) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": mensaje_sistema(catalogo)},
        {"role": "user", "content": mensaje_usuario(historia)},
    ]
