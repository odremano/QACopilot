# Diagrama de secuencia: exportación y ejecución

Flujo de RF-06 a RF-08 tal como está implementado en S5. El `.spec.ts` sale de las plantillas del catálogo y es el mismo archivo que se descarga y el que se ejecuta. Playwright corre en segundo plano, así que la interfaz no se bloquea.

## Exportación (RF-06)

```mermaid
sequenceDiagram
    autonumber
    actor QA as Analista QA
    participant FE as Frontend<br/>(Detalle de historia)
    participant API as Backend<br/>GET /historias/{id}/export
    participant EXP as services/exportador
    participant DB as PostgreSQL

    FE->>API: GET (si hay casos aprobados)
    API->>EXP: exportar_historia(historia, catálogo)
    EXP->>DB: casos «aprobado» de la historia
    alt no hay casos aprobados
        EXP-->>FE: 409 {"detalle"}
    else algún caso ya no coincide con el catálogo actual
        EXP-->>FE: 409 {"detalle": "CP-n está aprobado pero ya no es válido..."}
    else casos válidos
        Note over EXP: por cada paso: plantilla del catálogo<br/>+ valor como literal (json.dumps)<br/>dentro de un test.step
        EXP-->>API: HU-n.spec.ts
        API-->>FE: 200 text/plain (attachment)
        QA->>FE: Descargar .spec.ts / Ver el código
    end
```

## Ejecución y resultados (RF-07, RF-08)

```mermaid
sequenceDiagram
    autonumber
    actor QA as Analista QA
    participant FE as Frontend<br/>(Detalle y Ejecuciones)
    participant API as Backend<br/>/ejecuciones
    participant EJ as services/ejecuciones
    participant PW as Runner Playwright<br/>(Chromium headless)
    participant SUT as SauceDemo
    participant DB as PostgreSQL

    QA->>FE: Ejecutar pruebas
    FE->>API: POST /historias/{id}/ejecuciones
    API->>EJ: iniciar_ejecucion
    Note over EJ: arma el .spec.ts con el exportador
    EJ->>DB: INSERT ejecucion «en_curso»
    alt ya hay una en curso (índice único parcial)
        EJ-->>FE: 409 {"detalle": "Ya hay una ejecución en curso..."}
    else se crea
        API-->>FE: 202 ejecución «en_curso»
        API-)EJ: tarea en segundo plano

        par la interfaz sigue disponible
            loop cada 2 s (st.fragment) mientras esté en curso
                FE->>API: GET /ejecuciones/{id}
                API-->>FE: estado
            end
        and Playwright corre
            EJ->>PW: playwright test (1 worker, 30 s por test, tope 10 min)
            PW->>SUT: un test por caso, un test.step por paso
            SUT-->>PW: páginas
            PW-->>EJ: reporte.json + capturas de los fallos
            Note over EJ: cada test se asocia a su caso por [CP-n].<br/>Error sin ANSI y con el paso que falló.
            EJ->>DB: INSERT resultado_caso (aprobado / fallido / omitido)
            EJ->>DB: UPDATE ejecucion «finalizada» con totales y log
        end
        FE-->>QA: resumen y enlace al detalle
        QA->>FE: abrir el detalle
        FE->>API: GET /ejecuciones/{id}
        FE->>API: GET /evidencias/{resultado_id}
        API-->>FE: captura PNG del fallo
        FE-->>QA: resultado por caso, error y captura
    end
```

Si Playwright no genera el reporte, si el archivo no compila o si supera el tope de 10 minutos, la ejecución queda en «error» con el log. Si el backend se reinicia durante una ejecución, al arrancar la marca como «error» (`app/recuperar.py`), así la regla de una a la vez no bloquea las siguientes.

## Estados de la ejecución

```mermaid
stateDiagram-v2
    direction LR

    [*] --> en_curso : POST /historias/{id}/ejecuciones
    en_curso --> finalizada : reporte leído (resultados por caso)
    en_curso --> error : sin reporte, no compila, tiempo agotado o reinicio
    finalizada --> [*]
    error --> [*]

    note right of en_curso
        Solo una a la vez:
        índice único parcial
        ux_ejecucion_una_en_curso
    end note
```
