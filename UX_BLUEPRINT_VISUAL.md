# Blueprint Visual - PWR Rediseño UX/UI
## Wireframes Exactos + Mapa de Migración + Implementación Faseada

---

## 1. WIREFRAME TEXTUAL EXACTO - HOME

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  PORTABLE WORK ROUTER                                       │
│  Tu workspace para trabajo multi-LLM                        │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Proyectos recientes                                 │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │   │
│  │  │ Mi Proyecto  │  │ RosmarOps    │  │ + Nuevo  │  │   │
│  │  │              │  │              │  │ Proyecto │  │   │
│  │  │ 3 tareas     │  │ 5 tareas     │  │          │  │   │
│  │  │ 1 activo     │  │ 2 activos    │  │          │  │   │
│  │  │              │  │              │  │          │  │   │
│  │  │ [abrir]      │  │ [abrir]      │  │ [crear]  │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────┘  │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Buscar proyecto                                     │   │
│  │ [search input ──────────────────────────────────]  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Últimas tareas ejecutadas                           │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ • Explicar recursión (Mi Proyecto)       hace 2h   │   │
│  │   [ECO] ✓ Completada                               │   │
│  │                                                     │   │
│  │ • Estrategia escalado (Mi Proyecto)      hoy       │   │
│  │   [RACING] ✓ Completada                            │   │
│  │                                                     │   │
│  │ • SEO adversarial (RosmarOps)            ayer      │   │
│  │   [ECO] ✓ Completada                               │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘

DIMENSIONES Y PROPORCIONES:
- Ancho total: 100% viewport
- Padding: 2rem
- Título principal: 32px, bold
- Tarjetas: 3 columnas iguales, 200px de alto
- Últimas tareas: max-height 300px, scroll si necesario

JERARQUÍA VISUAL:
★★★ Proyectos recientes (tarjetas grandes)
★★  Buscar proyecto
★★  Últimas tareas (contexto)
★    "Crear proyecto" (dentro de tarjeta, no botón flotante)
```

---

## 2. WIREFRAME TEXTUAL EXACTO - PANTALLA DE PROYECTO

### 2.1 Vista completa (sin scroll)

```
┌────────────────────────────────────────────────────────────────┐
│ Home > Mi Proyecto                                      [close] │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────────────────┬──────────────────────────────┐  │
│  │                          │                              │  │
│  │ SIDEBAR                  │ ZONA DE TRABAJO              │  │
│  │ (ancho: 25%)             │ (ancho: 75%)                │  │
│  │                          │                              │  │
│  │ ┌────────────────────┐   │ ┌──────────────────────────┐ │  │
│  │ │ PROYECTO           │   │ │ ROUTER DECISION          │ │  │
│  │ ├────────────────────┤   │ ├──────────────────────────┤ │  │
│  │ │ Mi Proyecto        │   │ │ ECO                      │ │  │
│  │ │ 3 tareas           │   │ │ ▲                        │ │  │
│  │ │ 1 activo           │   │ │ Rápido + Barato          │ │  │
│  │ │ [editar ▼]         │   │ │                          │ │  │
│  │ │                    │   │ │ Razón:                   │ │  │
│  │ │ Objetivo: Sí       │   │ │ Complejidad baja, tarea  │ │  │
│  │ │ Contexto: Sí       │   │ │ simple. Priorizar        │ │  │
│  │ │ Reglas: Sí         │   │ │ velocidad.               │ │  │
│  │ └────────────────────┘   │ │                          │ │  │
│  │                          │ │ Modelo:                  │ │  │
│  │ ┌────────────────────┐   │ │ gemini-2.5-flash-lite   │ │  │
│  │ │ CAPTURA RÁPIDA     │   │ │                          │ │  │
│  │ ├────────────────────┤   │ │ Latencia: 234ms          │ │  │
│  │ │ ¿Qué necesitas?    │   │ │ Coste: $0.05             │ │  │
│  │ │ [input]  [crear]   │   │ │                          │ │  │
│  │ │                    │   │ │ [Cambiar a RACING]       │ │  │
│  │ │ ▼ Opciones         │   │ │ [Ver detalles ▼]         │ │  │
│  │ │ Tipo: [combo]      │   │ │                          │ │  │
│  │ │ Contexto: [text]   │   │ └──────────────────────────┘ │  │
│  │ │ Archivos: [upload] │   │                              │  │
│  │ └────────────────────┘   │ ┌──────────────────────────┐ │  │
│  │                          │ │ RESULTADO                │ │  │
│  │ ┌────────────────────┐   │ ├──────────────────────────┤ │  │
│  │ │ TAREAS (3)         │   │ │                          │ │  │
│  │ ├────────────────────┤   │ │ [output real de Gemini]  │ │  │
│  │ │ [búsqueda]         │   │ │                          │ │  │
│  │ │                    │   │ │ Lorem ipsum dolor sit    │ │  │
│  │ │ ▪ Tarea 1          │   │ │ amet, consectetur        │ │  │
│  │ │   hace 2h          │   │ │ adipiscing elit...       │ │  │
│  │ │                    │   │ │                          │ │  │
│  │ │ ▪ Tarea 2 ◄ ACT   │   │ │ [scroll]                 │ │  │
│  │ │   hace 1h          │   │ │                          │ │  │
│  │ │   [ejecutar]       │   │ │ ┌──────────────────────┐ │ │  │
│  │ │                    │   │ │ │ Extracto reusable    │ │ │  │
│  │ │ ▪ Tarea 3          │   │ │ │ [resumen]            │ │ │  │
│  │ │   ayer             │   │ │ └──────────────────────┘ │ │  │
│  │ │                    │   │                              │  │
│  │ │ [+ Nueva]          │   │ [Guardar] [Crear activo]     │  │
│  │ └────────────────────┘   │ [Editar] [Duplicar]          │  │
│  │                          │ [Ejecutar con Router]        │  │
│  │                          │                              │  │
│  │                          │ ▼ Expandibles (bajo demanda) │  │
│  │                          │ [▼ Ficha del proyecto...]    │  │
│  │                          │ [▼ Prompt sugerido...]       │  │
│  │                          │ [▼ Trazabilidad...]          │  │
│  │                          │ [▼ Activos relacionados...]  │  │
│  │                          │                              │  │
│  └──────────────────────────┴──────────────────────────────┘  │
│                                                                │
└────────────────────────────────────────────────────────────────┘

DIMENSIONES PRECISAS:
- Breadcrumb: 12px, muted
- Sidebar: 25% ancho, max-width 350px
- Main: 75% ancho, scrollable
- Router decision: altura ~180px
- Resultado: altura ~400px (scrollable internamente)
- Expandibles: height 0 (collapsed) → dinamico (expanded)
```

### 2.2 Estados de expandibles (bajo demanda)

```
CUANDO NO EXPANDIDO:
┌────────────────────────────────────────────────┐
│ [▼ Ficha del proyecto (editar)]                │
│ [▼ Prompt sugerido]                            │
│ [▼ Trazabilidad]                               │
│ [▼ Activos relacionados]                       │
└────────────────────────────────────────────────┘

CUANDO EXPANDIDO (ejemplo: Ficha):
┌────────────────────────────────────────────────┐
│ [▲ Ficha del proyecto (editar)]                │
│ ┌────────────────────────────────────────────┐ │
│ │ Objetivo:                                  │ │
│ │ [textarea grande]                          │ │
│ │                                            │ │
│ │ Contexto de referencia:                    │ │
│ │ [textarea grande]                          │ │
│ │                                            │ │
│ │ Reglas estables:                           │ │
│ │ [textarea grande]                          │ │
│ │                                            │ │
│ │ [Guardar cambios] [Cancelar]               │ │
│ └────────────────────────────────────────────┘ │
│                                                │
│ [▼ Prompt sugerido]                            │
│ [▼ Trazabilidad]                               │
│ [▼ Activos relacionados]                       │
└────────────────────────────────────────────────┘
```

---

## 3. JERARQUÍA VISUAL DE CADA BLOQUE

```
SIDEBAR - PROYECTO
┌─────────────────────────┐
│ Mi Proyecto             │ ← 16px, bold, primario
├─────────────────────────┤
│ 3 tareas | 1 activo     │ ← 12px, muted, metadata
│ [editar ▼]              │ ← 12px, link, acción
│                         │
│ Objetivo: Sí            │ ← 12px, indicador (no expandir aquí)
│ Contexto: Sí            │
│ Reglas: Sí              │
└─────────────────────────┘
Altura: ~120px
Padding: 1rem
Border: subtle (1px)
BG: panel light

SIDEBAR - CAPTURA
┌─────────────────────────┐
│ Captura rápida          │ ← 14px, bold, primario
├─────────────────────────┤
│ ¿Qué necesitas?         │ ← 12px, regular, label
│ [input] [crear]         │ ← input 80%, botón 20%
│                         │
│ ▼ Opciones              │ ← 11px, toggle
│ [contents si expandido]  │
└─────────────────────────┘
Altura: ~100px (collapsed) → ~200px (expanded)
Padding: 1rem
Border: subtle
BG: panel light

SIDEBAR - TAREAS
┌─────────────────────────┐
│ Tareas (3)              │ ← 14px, bold
│ [búsqueda]              │ ← input
├─────────────────────────┤
│ ▪ Tarea 1               │ ← 13px, regular
│   hace 2h               │ ← 11px, muted
│                         │
│ ▪ Tarea 2 ◄ ACTIVA      │ ← highlight
│   hace 1h               │
│   [ejecutar]            │ ← 11px, action link
│                         │
│ [+ Nueva]               │ ← 12px, link primario
└─────────────────────────┘
Altura: ~250px (scrollable)
Padding: 1rem
Border: subtle
BG: panel light

MAIN - ROUTER DECISION
┌──────────────────────────────────────┐
│ ECO                                  │ ← 32px, bold, color
│ ▲ Rápido + Barato                    │ ← 14px, descriptivo
│                                      │
│ Razón:                               │ ← 12px, bold, label
│ Complejidad baja, tarea simple.      │ ← 13px, regular
│ Priorizar velocidad.                 │
│                                      │
│ Modelo: gemini-2.5-flash-lite       │ ← 12px, code
│ Latencia: 234ms | Coste: $0.05      │ ← 12px, metrics
│                                      │
│ [Cambiar a RACING]                   │ ← 12px, link
│ [Ver detalles ▼]                     │ ← 12px, link
└──────────────────────────────────────┘
Altura: ~180px
Padding: 1.5rem
Border: 2px, color accent (eco/racing)
BG: panel highlight
Margin bottom: 2rem

MAIN - RESULTADO
┌──────────────────────────────────────┐
│ RESULTADO                            │ ← 16px, bold, label
├──────────────────────────────────────┤
│                                      │
│ [output real, editable]              │ ← 14px, monospace/regular
│                                      │
│ [contenido scrollable, ~350px]       │
│                                      │
│ ┌──────────────────────────────────┐ │
│ │ Extracto reusable                │ │ ← 12px, label
│ │ [contenido primeros 700 chars]   │ │ ← 12px, editable
│ └──────────────────────────────────┘ │
│                                      │
│ [Guardar] [Crear activo]             │ ← primary buttons
│ [Editar] [Duplicar]                  │ ← secondary buttons
└──────────────────────────────────────┘
Altura: ~400px (scrollable internamente)
Padding: 1.5rem
Border: 1px, subtle
BG: panel white
Margin bottom: 1.5rem

MAIN - EXPANDIBLES
┌──────────────────────────────────────┐
│ [▼ Ficha del proyecto (editar)]      │ ← 12px, toggle
│ [▼ Prompt sugerido]                  │
│ [▼ Trazabilidad]                     │
│ [▼ Activos relacionados]             │
│                                      │
│ (cuando expandido, content visible)  │
└──────────────────────────────────────┘
Altura: variable (36px per header + content)
Padding: 0.5rem
Border: 0
BG: transparent
```

---

## 4. VISIBLE POR DEFECTO vs BAJO DEMANDA

### HOME

| Elemento | Estado Default | Acción |
|----------|---|---|
| Título PWR | ✓ Visible | N/A |
| Proyectos recientes (tarjetas) | ✓ Visible | Click → ir a proyecto |
| Buscar proyecto | ✓ Visible | Input → filtrar |
| Últimas tareas | ✓ Visible | Scroll si muchas |
| Crear proyecto | ✓ Visible (dentro tarjeta) | Click → modal |

### PROJECT VIEW - SIDEBAR

| Elemento | Estado Default | Acción |
|----------|---|---|
| Contexto del proyecto | ✓ Visible (resumido) | [editar] → modal |
| Captura rápida | ✓ Visible (input + [crear]) | [Opciones ▼] → expandir |
| Opciones de captura | ✗ Expandible | Click [▼] → mostrar |
| Lista de tareas | ✓ Visible (scrollable) | Click tarea → cargar |
| Buscar tareas | ✓ Visible | Input → filtrar |
| Indicador "activa" | ✓ Visible (◄) | N/A |
| Botón "Nueva" | ✓ Visible | Click → crear |

### PROJECT VIEW - MAIN

| Elemento | Estado Default | Acción |
|----------|---|---|
| Breadcrumb | ✓ Visible (muted) | Click → volver |
| Router decision | ✓ Visible | [Cambiar RACING] → change |
| Resultado | ✓ Visible | Editable inline |
| Extracto | ✓ Visible | Editable inline |
| Botones primarios | ✓ Visible | Click → acción |
| Ficha del proyecto | ✗ Expandible | [▼] → expandir + modal editar |
| Prompt sugerido | ✗ Expandible | [▼] → expandir |
| Trazabilidad | ✗ Expandible | [▼] → expandir |
| Activos relacionados | ✗ Expandible | [▼] → expandir |

---

## 5. MAPA DE MIGRACIÓN: BLOQUE ACTUAL → NUEVA POSICIÓN

```
ARCHIVO: app.py

ACTUAL (POSICIÓN)                    →    NUEVO (POSICIÓN)
════════════════════════════════════════════════════════════════════

HOME:
─────

home_view()                          →    home_view() REESCRITO
- Mostrar solo info proyecto         →    - Proyectos recientes (tarjetas)
- [Crear proyecto]                   →    - Buscar proyecto
                                     →    - Últimas tareas ejecutadas

PROJECT VIEW:
─────────────

Sidebar (project_selector)
  [selector proyecto]                →    [selector proyecto] (mismo)

Main (project_view)
  ├─ Header                          →    Breadcrumb + [close]
  │
  ├─ Ficha del proyecto (expander)   →    SIDEBAR: Contexto resumido
  │  [editable inline]               →    [editar] → MODAL
  │
  ├─ LEFT COLUMN
  │  ├─ Captura (st.columns)         →    SIDEBAR: Captura rápida
  │  │  inputs 5 campos              →    input + [crear] + [▼ opciones]
  │  │
  │  ├─ Tareas (st.columns)          →    SIDEBAR: Lista de tareas
  │  │  lista inline                 →    lista scrollable con búsqueda
  │
  ├─ RIGHT COLUMN
  │  ├─ Decisión modelo (pequeña)    →    MAIN: Router Decision (panel)
  │  │  [expander]                   →    Visible, con [cambiar] y [detalles]
  │  │
  │  ├─ Prompt sugerido              →    MAIN: [▼ Expandible]
  │  │  [code block]                 →    Bajo demanda
  │  │
  │  ├─ Resultado (textareas)        →    MAIN: Panel Resultado
  │  │  output + extract             →    output editable + extract integrado
  │  │
  │  ├─ [Guardar] [Crear activo]     →    MAIN: Botones bajo resultado
  │  │
  │  ├─ Trazabilidad (expander)      →    MAIN: [▼ Expandible]
  │  │  [todos los datos]            →    Bajo demanda
  │  │
  │  └─ Activos recientes (abajo)    →    MAIN: [▼ Expandible]
  │     lista simple                 →    Bajo demanda

════════════════════════════════════════════════════════════════════
```

---

## 6. ORDEN EXACTO DE IMPLEMENTACIÓN EN app.py - FASEADO

### FASE 1: ESTRUCTURA BASE (1-2 horas)
**Objetivo:** Cambiar layout principal sin romper funcionalidad

```
1.1. Cambiar st.columns() layout
     ANTES:
       left, right = st.columns([1.1, 1.9])
       with left:
         [captura + tareas]
       with right:
         [resultado + trazabilidad]

     DESPUÉS:
       sidebar, main = st.columns([0.25, 0.75], gap="large")
       with sidebar:
         [proyecto + captura + tareas]
       with main:
         [router + resultado + expandibles]

1.2. Mover bloques de código (copy-paste, sin lógica nueva)
     - Captura: st.markdown + inputs → dentro sidebar
     - Tareas: lista → dentro sidebar
     - Router decision: pequeño box → main, arriba

1.3. Preservar todas las funciones
     - create_task() → sigue funcionando
     - update_task_result() → sigue funcionando
     - create_asset() → sigue funcionando
     - Router execution → sigue funcionando

CHECKLIST FASE 1:
✓ Layout cambiado (sidebar + main)
✓ Captura en sidebar
✓ Tareas en sidebar
✓ Router en main (arriba)
✓ Resultado en main (abajo)
✓ No hay errores de ejecución
✓ Datos se persisten
✓ Router funciona
```

### FASE 2: COMPACTAR CAPTURA (30 min)
**Objetivo:** De 5 campos visibles a 1 + opciones expandibles

```
2.1. Reorganizar estructura de captura
     ANTES:
       ├─ Título (input)
       ├─ Tipo (selectbox)
       ├─ Descripción (textarea)
       ├─ Contexto (textarea)
       ├─ Archivos (uploader)
       └─ [Crear]

     DESPUÉS:
       ├─ ¿Qué necesitas? (input) + [crear]
       └─ ▼ Opciones
          ├─ Tipo (selectbox)
          ├─ Contexto (textarea)
          └─ Archivos (uploader)

2.2. Cambiar en app.py (crear nueva función o refactorizar)
     - Nueva estructura: input principal + st.expander("Opciones")
     - El [crear] queda al lado del input (columnas internas)
     - Mantener la lógica de create_task()

CHECKLIST FASE 2:
✓ Captura compacta visualmente
✓ Opciones en expandible
✓ [crear] funciona igual
✓ create_task() sigue persistiendo
```

### FASE 3: ROUTER DECISION VISIBLE (1 hora)
**Objetivo:** De caja pequeña a panel central protagonista

```
3.1. Crear panel separado para Router decision
     ANTES:
       - Sección pequeña "Decisión de modelo"
       - Dentro de columnas

     DESPUÉS:
       - Panel destacado en top de main
       - Visible sin scroll
       - Mejor visual, más información

3.2. Implementar en app.py
     - Si hay tarea seleccionada, mostrar panel router prominente
     - Agregar [Cambiar a RACING] si está en eco
     - Agregar [Ver detalles ▼] para trazabilidad expandible
     - Mantener logic de trace_key en session_state

CHECKLIST FASE 3:
✓ Router decision visible arriba
✓ Botón cambio de modo funciona
✓ Trace_key sigue en session_state
✓ Trazabilidad expande bajo demanda
```

### FASE 4: RESULTADO COMO PROTAGONISTA (1 hora)
**Objetivo:** De bloque secundario a panel central

```
4.1. Reorganizar resultado en main
     ANTES:
       - Output + extract como textareas separadas
       - Botones abajo de todo
       - Activos al final

     DESPUÉS:
       - Output como textarea grande (foco visual)
       - Extract integrado dentro (sub-panel)
       - Botones bajo extracto (Guardar, Crear activo)
       - Acciones secundarias: Editar, Duplicar

4.2. Implementar en app.py
     - Cambiar st.text_area layout
     - Integrar extract dentro del resultado
     - Reorganizar botones en 2 niveles: primarios + secundarios
     - Mantener todas las funcionalidades de guardado

CHECKLIST FASE 4:
✓ Resultado visible como protagonista
✓ Extracto integrado
✓ Botones en jerarquía clara
✓ Guardar y Crear activo siguen funcionando
```

### FASE 5: EXPANDIBLES Y MODAL FICHA (1.5 horas)
**Objetivo:** Ficha proyecto y otros bajo demanda

```
5.1. Mover Ficha del proyecto a modal
     ANTES:
       - Expander inline que ocupa media pantalla

     DESPUÉS:
       - Contexto resumido en sidebar siempre visible
       - [editar] abre MODAL (st.modal o dialog pattern)
       - Tareas y edición no invaden workspace

5.2. Crear expandibles para info secundaria
     - [▼ Ficha del proyecto (editar)]
     - [▼ Prompt sugerido]
     - [▼ Trazabilidad] (ya existe, pero bajo demanda)
     - [▼ Activos relacionados]

5.3. Implementar en app.py
     - Nueva función: render_project_modal()
     - Reorganizar expanders
     - Modal se abre con [editar] en sidebar

CHECKLIST FASE 5:
✓ Ficha resumida en sidebar
✓ [editar] abre modal (no expande inline)
✓ Expandibles funcionales (expanders)
✓ Prompt, trazabilidad, activos bajo demanda
✓ No invaden workspace
```

### FASE 6: BREADCRUMB Y NAVEGACIÓN (30 min)
**Objetivo:** Contexto visual claro

```
6.1. Agregar breadcrumb
     - Home > Proyecto > (Tarea si existe)
     - Links funcionales
     - Muted visual (12px)

6.2. Agregar botón [close] o contexto
     - Volver a home o seleccionar otra tarea

CHECKLIST FASE 6:
✓ Breadcrumb visible
✓ Links funcionan
✓ [close] o navegación clara
```

### FASE 7: CSS Y PULIDO VISUAL (1-2 horas)
**Objetivo:** Jerarquía visual clara, professional B2B

```
7.1. Mejorar inject_css()
     - Padding/margin apropiados
     - Tipografía clara (tamaños jerárquicos)
     - Colores sobrios (B2B, sin emojis)
     - Espacios negativos
     - Bordes sutiles

7.2. Por elemento:
     - Titulo proyecto: 28px bold
     - Subtítulos: 16px bold
     - Labels: 12px regular
     - Metadata: 11px muted
     - Code: monospace
     - Links: color primario

7.3. Paneles:
     - Padding: 1.5rem
     - Border: 1px subtle
     - Border-radius: 4px
     - BG: panel light (casi blanco)
     - Sombra sutil

CHECKLIST FASE 7:
✓ Tipografía clara
✓ Espacios consistentes
✓ Colores sobrios (B2B)
✓ Sin emojis
✓ Visual professional
```

### FASE 8: VALIDACIÓN FINAL (1 hora)
**Objetivo:** Asegurar que nada se rompió

```
8.1. Tests funcionales
     ✓ Crear proyecto
     ✓ Crear tarea
     ✓ Ejecutar con Router
     ✓ Guardar resultado
     ✓ Crear activo
     ✓ Datos persisten en BD

8.2. Tests visuales
     ✓ Layout responsive
     ✓ Sin scroll innecesario
     ✓ Jerarquía clara
     ✓ Usable en diferentes tamaños

8.3. Tests de flujo
     ✓ Ruta: Home → Proyecto → Tarea → Resultado → Activo
     ✓ Cambio eco/racing funciona
     ✓ Expandibles funcionan
     ✓ Modal editar proyecto funciona

CHECKLIST FASE 8:
✓ Todos los tests pasan
✓ No hay errores en consola
✓ Funcionalidad preservada 100%
```

---

## RESUMEN DE IMPLEMENTACIÓN

| Fase | Tiempo | Qué | Riesgo |
|------|--------|-----|--------|
| 1 | 1.5h | Layout sidebar+main | Bajo (solo layout) |
| 2 | 0.5h | Captura compacta | Bajo (solo inputs) |
| 3 | 1h | Router visible | Bajo (ya existe) |
| 4 | 1h | Resultado protagonista | Bajo (solo reorganización) |
| 5 | 1.5h | Expandibles + Modal | Medio (nuevo patrón) |
| 6 | 0.5h | Breadcrumb | Bajo (solo display) |
| 7 | 1.5h | CSS y visual | Ninguno (solo styling) |
| 8 | 1h | Validación | Ninguno (testing) |
| **TOTAL** | **8.5h** | | |

---

## CAMBIOS EN app.py - RESUMEN POR FUNCIÓN

```
FUNCIONES QUE SE TOCAN (solo estructura, no lógica):
─────────────────────────────────────────────────

home_view()
  - CAMBIO: Completo rediseño (tarjetas recientes, búsqueda)
  - CONSERVA: Crear proyecto funciona igual
  - RIESGO: Bajo

project_view()
  - CAMBIO: Layout completo (sidebar + main)
  - CONSERVA: Todas las funciones de negocio
  - RIESGO: Medio (es la función más grande)

render_project_context() [NUEVA]
  - Mostrar contexto resumido en sidebar
  - Botón [editar] que abre modal

render_capture_form() [NUEVA O REFACTORIZADA]
  - Captura compacta con expandibles

render_project_modal() [NUEVA]
  - Modal para editar proyecto
  - Se abre desde [editar] en sidebar

render_task_list() [NUEVA O REFACTORIZADA]
  - Lista de tareas en sidebar
  - Con búsqueda y estado visual

render_router_decision() [NUEVA O REFACTORIZADA]
  - Panel Router decision prominente
  - Con botón cambio de modo

render_result() [NUEVA O REFACTORIZADA]
  - Resultado como protagonista
  - Extracto integrado
  - Botones jerarquizados

render_expandibles() [NUEVA O REFACTORIZADA]
  - Ficha, Prompt, Trazabilidad, Activos
  - Todos bajo demanda

FUNCIONES QUE NO SE TOCAN:
─────────────────────────

create_project()        ✓ Intacta
create_task()          ✓ Intacta
update_task_result()   ✓ Intacta
create_asset()         ✓ Intacta
get_project()          ✓ Intacta
get_task()             ✓ Intacta
save_execution_result()✓ Intacta
ExecutionService       ✓ Intacta
GeminiProvider         ✓ Intacta
```

---

## DIAGRAMA DE FLUJO - IMPLEMENTACIÓN

```
Inicio
  │
  ├─ FASE 1: Layout base
  │  └─ Sidebar + Main columns
  │     ├─ Captura → sidebar
  │     ├─ Tareas → sidebar
  │     └─ Router + Resultado → main
  │        └─ ✓ PUNTO DE CONTROL: Todo funciona
  │
  ├─ FASE 2: Captura compacta
  │  └─ Input principal + expandible opciones
  │     └─ ✓ PUNTO DE CONTROL: create_task() sigue igual
  │
  ├─ FASE 3: Router visible
  │  └─ Panel prominente en main
  │     └─ ✓ PUNTO DE CONTROL: Trace sigue en session_state
  │
  ├─ FASE 4: Resultado protagonista
  │  └─ Output + extract + botones
  │     └─ ✓ PUNTO DE CONTROL: Guardar/Crear activo funcionan
  │
  ├─ FASE 5: Expandibles
  │  └─ Modal + Expanders
  │     └─ ✓ PUNTO DE CONTROL: No invaden workspace
  │
  ├─ FASE 6: Breadcrumb
  │  └─ Navegación clara
  │     └─ ✓ PUNTO DE CONTROL: Links funcionan
  │
  ├─ FASE 7: CSS
  │  └─ Tipografía, espacios, colores
  │     └─ ✓ PUNTO DE CONTROL: Visual professional
  │
  └─ FASE 8: Validación
     └─ Tests funcionales y visuales
        └─ ✓ HITO: UX rediseñada exitosamente

FIN: PWR es un workspace, no un formulario
```

---

## CHECKLIST DE PRESERVACIÓN

Durante cada fase, verificar:

```
BACKEND:
□ Router decision funciona (eco/racing automático)
□ Datos se persisten en SQLite
□ create_task() inserta en BD
□ update_task_result() actualiza
□ create_asset() crea activos
□ Gemini API se ejecuta
□ White box muestra datos correctos

UI/UX:
□ Home muestra proyectos
□ Proyecto se abre
□ Tarea se selecciona
□ Resultado se muestra
□ Buttons funcionan
□ Expanders expandem/collapsan
□ Modal se abre/cierra

INTEGRIDAD:
□ No hay errores en consola
□ No hay warnings sin sentido
□ Performance sigue bueno
□ Responsive en diferentes tamaños
```

---

## PRÓXIMO PASO

Una vez validado este blueprint:

1. **Aprobación de wireframes** (¿son exactos?)
2. **Aprobación de flujo de implementación** (¿orden correcto?)
3. **Aprobación de puntos de control** (¿checklist completo?)
4. **Pasar a código detallado** (implementación fase por fase)

¿Validás el blueprint visual y el plan de faseado?
