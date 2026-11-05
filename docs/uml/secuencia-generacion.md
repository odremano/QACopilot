# Diagrama de secuencia: generación y revisión de casos

Flujo de RF-03 a RF-05 tal como está implementado en S4. El LLM solo propone pasos en JSON: el backend arma el Gherkin, lo valida contra el catálogo y la persona decide qué se aprueba.

## Generación con IA (RF-03, RF-04)

```mermaid
sequenceDiagram
    autonumber
    actor QA as Analista QA
    participant FE as Frontend<br/>(Detalle de historia)
    participant API as Backend<br/>POST /historias/{id}/generaciones
    participant GEN as services/generaciones
    participant VAL as services/validador
    participant LLM as Proveedor LLM<br/>(OpenRouter o demo)
    participant DB as PostgreSQL

    QA->>FE: Generar casos
    FE->>API: POST (timeout 300 s)
    API->>GEN: generar_casos(historia, proveedor, catálogo)
    GEN->>DB: historia y generaciones del día
    alt la historia no existe
        GEN-->>FE: 404 {"detalle"}
    else se alcanzó DAILY_GENERATION_LIMIT (RNF-08)
        GEN-->>FE: 429 {"detalle"}
    end
    Note over GEN: prompt v1 = reglas + catálogo<br/>agrupado + contexto del SUT + ejemplo

    loop hasta 3 intentos
        GEN->>LLM: mensajes (salida json_object)
        alt error del proveedor (clave, crédito, timeout)
            LLM-->>GEN: ErrorProveedor
            Note over GEN: no se reintenta
        else respuesta recibida
            LLM-->>GEN: {"casos": [{titulo, tipo, pasos}]}
            GEN->>VAL: validar_respuesta(contenido, catálogo)
            Note over VAL: JSON y esquema → arma «Escenario:» + pasos<br/>→ sintaxis Gherkin → cada paso contra el catálogo
            VAL-->>GEN: casos con valido y errores
            Note over GEN: reglas de la generación: 3 a 8 casos,<br/>al menos un positivo y un negativo.<br/>Si fallan el JSON o estas reglas, reintenta.
        end
    end

    GEN->>DB: INSERT generacion (intentos crudos, duración, estado)
    alt la generación falló
        GEN-->>FE: 502 {"detalle": "... Se intentó 3 veces."}
        FE-->>QA: mensaje de error
    else la generación salió bien
        GEN->>DB: borra los casos pendientes anteriores
        GEN->>DB: INSERT casos «pendiente» (los inválidos con sus errores)
        GEN-->>API: GeneracionSalida
        API-->>FE: 201 casos, casos_validos, casos_invalidos
        FE-->>QA: tarjetas ✅ válidas y ⚠️ inválidas
    end
```

Un caso es inválido cuando un paso no coincide con ningún patrón del catálogo, aunque el JSON sea correcto. Queda guardado igual, con sus errores, para que la persona lo corrija o lo descarte. Al regenerar se conservan los casos aprobados y descartados (RF-11).

## Revisión humana (RF-05)

```mermaid
sequenceDiagram
    autonumber
    actor QA as Analista QA
    participant FE as Frontend<br/>(tarjeta del caso)
    participant API as Backend<br/>/casos/{id}
    participant CAS as services/casos
    participant VAL as services/validador
    participant DB as PostgreSQL

    opt el caso es inválido
        QA->>FE: Editar y Guardar y revalidar
        FE->>API: PUT /casos/{id} {"gherkin"}
        API->>CAS: editar_caso
        alt el caso no está pendiente
            CAS-->>FE: 409 {"detalle"}
        else pendiente
            CAS->>VAL: validar_gherkin(texto, catálogo)
            VAL-->>CAS: errores (vacío si es válido)
            CAS->>DB: UPDATE gherkin, valido, errores y título
            CAS-->>FE: 200 caso revalidado
        end
    end

    QA->>FE: Aprobar (deshabilitado si es inválido)
    FE->>API: POST /casos/{id}/aprobar
    API->>CAS: cambiar_estado("aprobar")
    alt no está pendiente o no es válido
        CAS-->>FE: 409 {"detalle"}
    else pendiente y válido
        CAS->>DB: UPDATE estado = aprobado
        CAS-->>FE: 200 caso aprobado
    end
    FE-->>QA: aviso dentro de la tarjeta y contadores actualizados
```

Descartar y volver a pendiente siguen el mismo camino con `POST /casos/{id}/descartar` y `POST /casos/{id}/pendiente`. Las transiciones permitidas están en el [diagrama de estados](estados-caso.md).
