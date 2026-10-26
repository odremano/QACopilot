# Diagrama de clases (modelo de dominio)

Las cinco entidades persistidas en PostgreSQL (spec, sección 8) con sus atributos, multiplicidades y los valores válidos de cada estado. Los identificadores visibles `HU-n` y `CP-n` se calculan a partir del `id`; no se guardan.

```mermaid
classDiagram
    direction LR

    class HistoriaUsuario {
        +int id
        +String titulo
        +Text descripcion
        +Optional~Text~ criterios_aceptacion
        +DateTime creada_en
        +DateTime actualizada_en
        +codigo() String
    }

    class Generacion {
        +int id
        +int historia_id
        +String proveedor
        +String modelo
        +String version_prompt
        +EstadoGeneracion estado
        +Optional~int~ duracion_ms
        +Optional~JSONB~ respuesta_cruda
        +Optional~Text~ mensaje_error
        +DateTime creada_en
    }

    class CasoPrueba {
        +int id
        +int historia_id
        +Optional~int~ generacion_id
        +String titulo
        +TipoCaso tipo
        +Text gherkin
        +EstadoCaso estado
        +bool valido
        +Optional~JSONB~ errores_validacion
        +DateTime creado_en
        +DateTime actualizado_en
        +codigo() String
    }

    class Ejecucion {
        +int id
        +int historia_id
        +EstadoEjecucion estado
        +DateTime iniciada_en
        +Optional~DateTime~ finalizada_en
        +int total
        +int aprobados
        +int fallidos
        +int omitidos
        +Optional~Text~ log
    }

    class ResultadoCaso {
        +int id
        +int ejecucion_id
        +int caso_id
        +EstadoResultado estado
        +Optional~int~ duracion_ms
        +Optional~Text~ mensaje_error
        +Optional~String~ ruta_captura
    }

    class EstadoGeneracion {
        <<enumeration>>
        ok
        error
    }
    class TipoCaso {
        <<enumeration>>
        positivo
        negativo
        limite
    }
    class EstadoCaso {
        <<enumeration>>
        pendiente
        aprobado
        descartado
    }
    class EstadoEjecucion {
        <<enumeration>>
        en_curso
        finalizada
        error
    }
    class EstadoResultado {
        <<enumeration>>
        aprobado
        fallido
        omitido
    }

    HistoriaUsuario "1" *-- "0..*" Generacion : genera
    HistoriaUsuario "1" *-- "0..*" CasoPrueba : contiene
    HistoriaUsuario "1" *-- "0..*" Ejecucion : registra
    Generacion "0..1" o-- "0..*" CasoPrueba : produce
    Ejecucion "1" *-- "0..*" ResultadoCaso : incluye
    CasoPrueba "1" *-- "0..*" ResultadoCaso : obtiene

    Generacion ..> EstadoGeneracion
    CasoPrueba ..> TipoCaso
    CasoPrueba ..> EstadoCaso
    Ejecucion ..> EstadoEjecucion
    ResultadoCaso ..> EstadoResultado
```

Composición (`*--`): al borrar la historia se borran en cascada sus generaciones, casos y ejecuciones (`ON DELETE CASCADE`). Agregación (`o--`): si se borra una generación, sus casos se conservan con `generacion_id` en nulo.
