# Diagrama de casos de uso

Casos de uso del MVP de QA Copilot con sus actores (spec, secciones 2.3 y 5). Mermaid no tiene un diagrama de casos de uso nativo: se representa con un *flowchart* donde los rectángulos son actores, los óvalos son casos de uso y el recuadro es el límite del sistema.

```mermaid
flowchart LR
    analista["Analista QA<br/>(actor)"]
    admin["Administrador<br/>(actor)"]
    llm["Proveedor LLM<br/>DeepSeek / Ollama<br/>(sistema externo)"]
    sut["SauceDemo<br/>(sistema externo · SUT)"]

    subgraph sistema["QA Copilot"]
        direction TB
        uc1(["Gestionar historias de usuario<br/>RF-01"])
        uc2(["Generar casos con IA<br/>RF-03 · RF-11"])
        uc3(["Validar casos<br/>RF-04"])
        uc4(["Revisar casos<br/>RF-05"])
        uc5(["Exportar a Playwright<br/>RF-06"])
        uc6(["Ejecutar pruebas<br/>RF-07 · RF-08"])
        uc7(["Consultar panel y resultados<br/>RF-09 · RF-12"])
        uc8(["Consultar catálogo de pasos<br/>RF-02"])
        uc9(["Configurar el sistema<br/>proveedor, límites, despliegue"])
    end

    analista --- uc1
    analista --- uc2
    analista --- uc4
    analista --- uc5
    analista --- uc6
    analista --- uc7
    analista --- uc8
    admin --- uc9

    uc2 -. "«include»" .-> uc3
    uc4 -. "«include»<br/>(al editar)" .-> uc3

    uc2 --- llm
    uc6 --- sut
```
