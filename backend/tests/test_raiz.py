"""La raíz de la API redirige a la documentación interactiva."""


def test_raiz_redirige_a_docs(client):
    respuesta = client.get("/", follow_redirects=False)

    assert respuesta.status_code == 307
    assert respuesta.headers["location"] == "/docs"
