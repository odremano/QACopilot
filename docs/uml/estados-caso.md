# Diagrama de estados del caso de prueba

Ciclo de vida de un caso de prueba durante la revisión humana (spec, sección 8.1 y RF-05). El atributo `valido` lo calcula el validador (RF-04) y condiciona la aprobación.

```mermaid
stateDiagram-v2
    direction LR

    [*] --> pendiente : generación con IA
    pendiente --> pendiente : editar (revalida)
    pendiente --> aprobado : aprobar [solo si es válido]
    pendiente --> descartado : descartar
    aprobado --> pendiente : volver a pendiente
    descartado --> pendiente : volver a pendiente

    note right of pendiente
        La edición solo se permite en pendiente
        y siempre revalida el caso.
    end note

    note right of aprobado
        Solo los casos aprobados
        se exportan y se ejecutan.
    end note
```
