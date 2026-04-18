════════════════════════════════════════════════════════════════════════════════
BLOQUE H: TRANSFORMACIÓN VISUAL (ANTES / DESPUÉS)
════════════════════════════════════════════════════════════════════════════════

════════════════════════════════════════════════════════════════════════════════
ESCENA 1: USER ACABA DE EJECUTAR UNA TAREA
════════════════════════════════════════════════════════════════════════════════

ANTES (G1-G4):
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  [Resultado de la ejecución...]                                 │
│  Lorem ipsum dolor sit amet, consectetur adipiscing elit...      │
│                                                                  │
│  [Copiar]  [Otra]  [Proyecto]  [X]                             │
│                                                                  │
│  → User piensa: "¿Dónde quedó esto?" "¿Se guardó?"             │
│    SENSACIÓN: Frágil, temporal, no confío                      │
└──────────────────────────────────────────────────────────────────┘


DESPUÉS (H implementado):
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│ ### 📋 Resultado                                                │
│ [Resultado de la ejecución...]                                 │
│ Lorem ipsum dolor sit amet, consectetur adipiscing elit...      │
│                                                                  │
│ ───────────────────────────────────────────────────────────     │
│ ✅ Guardado                                                      │
│ En: **Mi primer proyecto**                                       │
│ Tarea: **Resume un documento**                                   │
│ ───────────────────────────────────────────────────────────     │
│                                                                  │
│ [📂 Ver en proyecto]  ← PRIMARY, llamada clara                 │
│                                                                  │
│ Más acciones:                                                    │
│ [🔄 Usar como contexto] [🎯 Crear tarea relacionada]           │
│                                                                  │
│ ▼ 📋 Copiar resultado                                            │
│   [Texto copiable...]                                           │
│                                                                  │
│ → User piensa: "Está aquí, seguro, en proyecto X, tarea Y"     │
│   "¿Qué hago ahora? Ver proyecto o crear relacionada"          │
│   SENSACIÓN: Tranquila, segura, continuidad clara              │
└──────────────────────────────────────────────────────────────────┘

CAMBIO DE SENTIMIENTO:
❌ "¿Dónde quedó? Desapareció" → ✅ "Aquí guardado, puedo continuar"


════════════════════════════════════════════════════════════════════════════════
ESCENA 2: USER ABRE PWR AL DÍA SIGUIENTE (HOME)
════════════════════════════════════════════════════════════════════════════════

ANTES (G1-G4):
┌──────────────────────────────────────────────────────────────────┐
│ ### 🏠 Mis tareas                                               │
│                                                                  │
│ #### Trabajo en progreso                                        │
│ ┌────────────┐ ┌────────────┐ ┌────────────┐                   │
│ │📌 Resume   │ │📌 Escribe  │ │📌 Analiza  │                   │
│ │documento   │ │email       │ │gráfico     │                   │
│ │Mi proyecto │ │Mi proyecto │ │Mi proyecto │                   │
│ │[Continuar] │ │[Continuar] │ │[Continuar] │                   │
│ └────────────┘ └────────────┘ └────────────┘                   │
│                                                                  │
│ #### Mis proyectos                                              │
│ ┌──────────────────┐ ┌──────────────────┐                       │
│ │📁 Mi proyecto    │ │📁 Otro proyecto  │                       │
│ │3 tareas          │ │5 tareas          │                       │
│ │[Abrir]           │ │[Abrir]           │                       │
│ └──────────────────┘ └──────────────────┘                       │
│                                                                  │
│ → User piensa: "¿Qué hice ayer? ¿Qué es reciente?"             │
│   SENSACIÓN: Grids genéricos, no hay tiempo, no hay historia   │
└──────────────────────────────────────────────────────────────────┘


DESPUÉS (H implementado):
┌──────────────────────────────────────────────────────────────────┐
│ ### 🏠 Mis tareas                                               │
│                                                                  │
│ #### Hoy                                  ← NEW SECTION         │
│ ✅ Resume un documento                                           │
│    Mi primer proyecto · hace 2 horas                            │
│    [→]                                                           │
│                                                                  │
│ ✅ Escribe un email                                              │
│    Mi primer proyecto · hace 1 hora                             │
│    [→]                                                           │
│                                                                  │
│ ─────────────────────────────────────────────────────────       │
│                                                                  │
│ #### Trabajo en progreso                                        │
│ ┌────────────┐ ┌────────────┐ ┌────────────┐                   │
│ │📌 Analiza  │ │           │ │            │                   │
│ │gráfico     │ │           │ │            │                   │
│ │Mi proyecto │ │           │ │            │                   │
│ │[Continuar] │ │           │ │            │                   │
│ └────────────┘ └────────────┘ └────────────┘                   │
│                                                                  │
│ #### Mis proyectos                                              │
│ ┌──────────────────┐ ┌──────────────────┐                       │
│ │📁 Mi proyecto    │ │📁 Otro proyecto  │                       │
│ │3 tareas          │ │5 tareas          │                       │
│ │[Abrir]           │ │[Abrir]           │                       │
│ └──────────────────┘ └──────────────────┘                       │
│                                                                  │
│ → User piensa: "Hoy ejecuté 2 tareas (hace 2h y 1h)"            │
│   "Si necesito, las veo acá. Tengo 1 pendiente: Analiza"       │
│   SENSACIÓN: Timeline clara, veo mi actividad, continuidad      │
└──────────────────────────────────────────────────────────────────┘

CAMBIO DE SENTIMIENTO:
❌ "No sé qué es reciente, todo es un grid"
→ ✅ "Veo qué hice hoy, cuándo, en qué orden"


════════════════════════════════════════════════════════════════════════════════
ESCENA 3: USER ABRE UN PROYECTO
════════════════════════════════════════════════════════════════════════════════

ANTES (G1-G4):
┌──────────────────────────────────────────────────────────────────┐
│ Proyecto: Mi primer proyecto                      [Cerrar]       │
│ ──────────────────────────────────────────────────────────        │
│                                                                  │
│ SIDEBAR:                                                         │
│ ┌──────────────────────────────────────────────────────────┐    │
│ │ Trabajando en: **Mi primer proyecto**                   │    │
│ │                                                          │    │
│ │ ### ¿Qué necesitas hacer ahora?                         │    │
│ │ [INPUT area...]                                         │    │
│ │                                                          │    │
│ │ ### Tareas activas (3)                                  │    │
│ │ - Resume documento                                      │    │
│ │   [Abrir]                                               │    │
│ │ - Escribe email                                         │    │
│ │   [Abrir]                                               │    │
│ │ - Analiza gráfico                                       │    │
│ │   [Abrir]                                               │    │
│ │ → No se ve cuál tiene resultado                         │    │
│ │   SENSACIÓN: Lista sin contexto                         │    │
│ └──────────────────────────────────────────────────────────┘    │
│                                                                  │
│ MAIN:                                                            │
│ [Task detail si hay una seleccionada]                           │
└──────────────────────────────────────────────────────────────────┘


DESPUÉS (H implementado):
┌──────────────────────────────────────────────────────────────────┐
│ Proyecto: Mi primer proyecto                      [Cerrar]       │
│ ──────────────────────────────────────────────────────────        │
│                                                                  │
│ SIDEBAR:                                                         │
│ ┌──────────────────────────────────────────────────────────┐    │
│ │ Trabajando en: **Mi primer proyecto**                   │    │
│ │                                                          │    │
│ │ ### ¿Qué necesitas hacer ahora?                         │    │
│ │ [INPUT area...]                                         │    │
│ │                                                          │    │
│ │ ### Tareas (3)                     ← Conteo actualizado │    │
│ │                                                          │    │
│ │ #### ✅ Ejecutadas          ← NEW SECTION              │    │
│ │ Resume documento                                        │    │
│ │ Pensar                                                  │    │
│ │ 📋 Resultado disponible    ← Badge que muestra historial│    │
│ │ [Abrir]                                                 │    │
│ │                                                          │    │
│ │ Escribe email                                           │    │
│ │ Pensar                                                  │    │
│ │ 📋 Resultado disponible                                 │    │
│ │ [Abrir]                                                 │    │
│ │                                                          │    │
│ │ #### 📌 Pendientes         ← NEW SECTION               │    │
│ │ Analiza gráfico                                         │    │
│ │ Pensar                                                  │    │
│ │ [Abrir]                                                 │    │
│ │ → CLARO: 2 ejecutadas, 1 pendiente                     │    │
│ │   SENSACIÓN: Workspace con historia                    │    │
│ └──────────────────────────────────────────────────────────┘    │
│                                                                  │
│ MAIN:                                                            │
│ [Task detail si hay una seleccionada]                           │
└──────────────────────────────────────────────────────────────────┘

CAMBIO DE SENTIMIENTO:
❌ "Lista plana, no sé qué se hizo"
→ ✅ "Veo ejecutadas con resultados, veo pendientes, es un workspace"


════════════════════════════════════════════════════════════════════════════════
SÍNTESIS: TRANSFORMACIÓN GLOBAL
════════════════════════════════════════════════════════════════════════════════

ÁREA               ANTES                           DESPUÉS
──────────────────────────────────────────────────────────────────────────────

RESULTADO          "¿Dónde quedó esto?"            ✅ Guardado visible
POST-EXEC          Botones genéricos              Acciones jerárquicas
                   Sin contexto                    Con proyecto + tarea
                   SENSACIÓN: Frágil               SENSACIÓN: Segura

HOME               Grids sin tiempo                "Hoy" con timeline
                   No hay historial               Veo qué hice hoy
                   Sin continuidad                Timestamps claros
                   SENSACIÓN: Temporal             SENSACIÓN: Continua

PROYECTO           Lista plana                     Ejecutadas vs Pendientes
                   No se ve qué se hizo           Badges de resultados
                   Sin historia                    Workspace visible
                   SENSACIÓN: Tareas               SENSACIÓN: Workspace

SENSACIÓN          "Tool que ejecuta y             "Workspace donde mi
GLOBAL             desaparece"                     trabajo queda guardado"

                   Temporal, stateless             Persistente, memoriado
                   Baja confianza                  Alta confianza
                   Cada sesión es "nueva"          Continuidad clara


════════════════════════════════════════════════════════════════════════════════
MÉTRICA DE IMPACTO
════════════════════════════════════════════════════════════════════════════════

Pregunta Test        ANTES                          DESPUÉS
────────────────────────────────────────────────────────────────────────────────

"¿Dónde quedó?"     ❌ No sé, desapareció          ✅ En X proyecto, Y tarea

"¿Qué hoy?"         ❌ Tengo que buscar            ✅ Home/Hoy muestra activ.

"¿Reutilizable?"    ❌ Solo copiar texto           ✅ 3 opciones claras

"¿Qué sigue?"       ❌ No sé, quedé aquí           ✅ Ver proyecto → continúo

"¿Proyecto estado?" ❌ Lista sin contexto          ✅ Ejecutadas/pendientes

"¿Vuelvo atrás?"    ❌ No está                     ✅ Home/proyecto lo muestra

CONVERSIÓN GLOBAL   ❌ "Herramienta"               ✅ "Workspace con memoria"

════════════════════════════════════════════════════════════════════════════════
