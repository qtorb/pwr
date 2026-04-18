# HITO A: MICROPLAN EJECUTABLE

**Fecha**: 2026-04-18
**Status**: Listo para implementación
**Duración estimada**: 7 días laborales
**Criterio de éxito**: Usuario no se pierde. Sabe dónde está. Flujo es lineal.

---

## 1. PARTES CONCRETAS QUE TOCA HITO A

### Cambios en app.py (Streamlit principal)

**Eliminar:**
- `st.sidebar` completamente (todas las referencias)
- Menú lateral: "Home", "Proyectos", "Radar", "Settings"
- Navegación de proyecto desde sidebar
- Acceso a "Nueva Tarea" desde sidebar

**Modificar:**
- Layout: Cambiar de `st.set_page_config(layout="wide")` a estructura centrada
- Crear header superior compacto (logo + breadcrumb)
- Definir estados explícitos: `page` variable dicta qué se muestra

**Archivo**:
```
pwr/app.py (lineas ~1-50, set_page_config y layout)
pwr/app.py (lineas ~100-200, estructura principal if/elif por page)
```

### Componentes a crear o refactorizar

**Nuevos componentes** (van en `pwr/components/`):

1. `header.py`
   - Función: `render_header(proyecto=None, tarea=None, estado=None)`
   - Output: Logo + Breadcrumb + Usuario/Salir
   - NO debe renderizar navegación lateral

2. `breadcrumb.py`
   - Función: `render_breadcrumb(proyecto, tarea, estado_actual)`
   - Estados: "Home", "Proyecto", "Nueva Tarea", "Propuesta", "Resultado"
   - Click en breadcrumb navega (no implementar nav aún; solo estructura)

**Existentes a refactorizar**:

1. `home.py`
   - Cambio: Mostrar "Proyectos recientes" + "Nueva Tarea" (no sidebar)
   - Eliminar: Links a sidebar, navegación lateral
   - Output: Dos secciones claras, una acción principal cada una

2. `new_task.py`
   - Cambio: Full screen (no sidebar)
   - Eliminar: Navegación lateral
   - Output: Campo de tarea, selector de proyecto, botón "Ver propuesta"

3. `proposal.py` (si existe)
   - Cambio: Mostrar Modo | Modelo | Motivo (structure fixed)
   - No cambia lógica de propuesta, solo presentación

4. `result.py` (si existe)
   - Cambio: Mostrar modelo usado, tiempo, coste (Hito B implementa esto)
   - Por ahora: Solo layout, datos vienen del router

---

## 2. ORDEN PRECISO DE IMPLEMENTACIÓN

### **Fase 1: Estructura (Día 1-2)**

**Paso 1a**: Crear `pwr/components/header.py`
```python
def render_header(proyecto=None, tarea=None, estado=None):
    col1, col2, col3 = st.columns([1, 4, 1])

    with col1:
        st.markdown("**PWR**", unsafe_allow_html=True)

    with col2:
        # Breadcrumb será: PWR > Proyecto > Tarea > Estado
        # Por ahora: estructura, sin clicks funcionales
        breadcrumb_text = "PWR"
        if proyecto:
            breadcrumb_text += f" > {proyecto}"
        if tarea:
            breadcrumb_text += f" > {tarea}"
        if estado:
            breadcrumb_text += f" > {estado}"
        st.caption(breadcrumb_text)

    with col3:
        if st.button("Salir", key="logout"):
            # Implementar logout (Hito 2)
            pass
```

**Paso 1b**: Crear `pwr/components/breadcrumb.py`
```python
def render_breadcrumb(proyecto=None, tarea=None, estado=None):
    # Helper para breadcrumb (usado por header)
    # Estados válidos: "Home", "Proyecto", "Nueva Tarea", "Propuesta", "Resultado"

    items = ["PWR"]
    if proyecto:
        items.append(proyecto)
    if tarea:
        items.append(tarea)
    if estado:
        items.append(f"[{estado}]")  # Marca estado actual

    return " > ".join(items)
```

**Paso 1c**: Refactorizar `pwr/app.py` - Eliminar sidebar
```python
# ANTES (ELIMINAR):
with st.sidebar:
    st.markdown("## PWR")
    page = st.radio("Navegar", ["Home", "Proyectos", "Radar"])
    ...

# DESPUÉS (REEMPLAZAR):
# No hay sidebar
# `page` viene de st.session_state["current_page"]
# por defecto: "home"

from components.header import render_header

# Header siempre aparece
render_header(proyecto=st.session_state.get("proyecto"),
              tarea=st.session_state.get("tarea"),
              estado=st.session_state.get("estado"))

# Estructura principal por page
if st.session_state.get("current_page") == "home":
    from pages.home import render_home
    render_home()
elif st.session_state.get("current_page") == "new_task":
    from pages.new_task import render_new_task
    render_new_task()
elif st.session_state.get("current_page") == "proposal":
    from pages.proposal import render_proposal
    render_proposal()
elif st.session_state.get("current_page") == "result":
    from pages.result import render_result
    render_result()
```

**Validación al terminar Fase 1:**
- ✅ Sidebar no aparece en ninguna pantalla
- ✅ Header aparece en todas las pantallas
- ✅ Breadcrumb se actualiza según estado
- ✅ Logo + Usuario visibles en header

---

### **Fase 2: Home Rediseñado (Día 2-3)**

**Paso 2a**: Refactorizar `pwr/pages/home.py`
```python
def render_home():
    st.session_state["current_page"] = "home"
    st.session_state["estado"] = "Home"

    # Titulo
    st.markdown("# Workspace")

    # Sección 1: Proyectos recientes
    st.markdown("## Proyectos recientes")

    # Query: últimos 5 proyectos
    proyectos = get_recent_projects(limit=5)  # DB query

    for proyecto in proyectos:
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            st.markdown(f"**{proyecto['name']}**")
            ultima_tarea = get_last_task(proyecto['id'])
            if ultima_tarea:
                st.caption(f"Última: {ultima_tarea['title']} ({time_ago(ultima_tarea['timestamp'])})")
        with col3:
            if st.button("Abrir", key=f"open_proj_{proyecto['id']}"):
                st.session_state["current_page"] = "proyecto"
                st.session_state["proyecto_id"] = proyecto['id']
                st.rerun()

    st.divider()

    # Sección 2: Nueva Tarea
    st.markdown("## Nueva tarea")

    task_input = st.text_input("¿Qué tarea tienes hoy?", key="new_task_home")

    if st.button("Crear", key="create_task_btn"):
        if task_input.strip():
            st.session_state["task_title"] = task_input
            st.session_state["current_page"] = "new_task"
            st.rerun()
        else:
            st.error("Por favor, describe tu tarea")
```

**Validación al terminar Fase 2:**
- ✅ Home muestra solo dos cosas: Proyectos recientes + Nueva Tarea
- ✅ Click en proyecto abre Proyecto (sin implementar aún; solo navega a estado)
- ✅ Click en "Crear" abre Nueva Tarea

---

### **Fase 3: Nueva Tarea (Día 3-4)**

**Paso 3a**: Refactorizar `pwr/pages/new_task.py`
```python
def render_new_task():
    st.session_state["current_page"] = "new_task"
    st.session_state["estado"] = "Nueva Tarea"

    # Proyecto context (si viene de Home, ya está seteado)
    if "proyecto_id" not in st.session_state:
        # Mostrar selector
        proyectos = get_all_projects()
        proyecto_id = st.selectbox(
            "Proyecto",
            options=[p['id'] for p in proyectos],
            format_func=lambda id: next(p['name'] for p in proyectos if p['id'] == id),
            key="project_selector"
        )
        st.session_state["proyecto_id"] = proyecto_id

    # Formulario de tarea
    col1, _ = st.columns([2, 1])
    with col1:
        title = st.text_input("Título de la tarea", key="task_title_input")
        description = st.text_area("Descripción / contexto", key="task_description_input", height=100)

    st.divider()

    # Botón principal
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Ver propuesta", key="view_proposal_btn", use_container_width=True):
            if title.strip():
                # Guardar tarea en sesión (no en DB aún)
                st.session_state["task_title"] = title
                st.session_state["task_description"] = description
                st.session_state["current_page"] = "proposal"
                st.rerun()
            else:
                st.error("Por favor, describe tu tarea")

    with col2:
        if st.button("Cancelar", key="cancel_task_btn"):
            st.session_state["current_page"] = "home"
            st.rerun()
```

**Validación al terminar Fase 3:**
- ✅ Nueva Tarea es full screen (sin sidebar)
- ✅ Solo dos botones: "Ver propuesta" (principal) + "Cancelar"
- ✅ Campos claros: Título, Descripción, Proyecto

---

### **Fase 4: Estructura de Propuesta (Día 4-5)**

**Paso 4a**: Refactorizar `pwr/pages/proposal.py` (solo estructura visual, sin lógica nueva)
```python
def render_proposal():
    st.session_state["current_page"] = "proposal"
    st.session_state["estado"] = "Propuesta"

    proyecto = get_project(st.session_state["proyecto_id"])

    # Mostrar resumen de tarea
    st.markdown(f"### {st.session_state['task_title']}")
    st.caption(st.session_state.get("task_description", ""))

    st.divider()

    # BLOQUE DE RECOMENDACIÓN (estructura fija)
    st.markdown("### RECOMENDACIÓN DE PWR")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Modo**")
        st.markdown("ECO")  # Por ahora hardcoded; Router decide después

    with col2:
        st.markdown("**Modelo**")
        st.markdown("Gemini 2.5 Flash Lite")  # Por ahora hardcoded

    with col3:
        st.markdown("**Por qué**")
        st.markdown("Tarea clara, prioridad rapidez")  # Por ahora hardcoded

    st.divider()

    # Botón principal
    if st.button("Ejecutar", key="execute_btn", use_container_width=True):
        st.session_state["current_page"] = "executing"  # Estado temporal
        st.rerun()
```

**Validación al terminar Fase 4:**
- ✅ Bloque de propuesta tiene estructura fija: Modo | Modelo | Por qué
- ✅ Botón "Ejecutar" es protagonista
- ✅ Propuesta viene de Router (Hito B implementa lógica real)

---

### **Fase 5: Validación e Integración (Día 5-7)**

**Paso 5a**: Integración de flujo completo

```python
# en app.py, garantizar que estados están conectados:

# Home → Nueva Tarea ✅
# Nueva Tarea → Propuesta ✅
# Propuesta → Ejecutar (todavía no implementa; solo estructura)
# Ejecutar → Resultado (Hito B)
```

**Paso 5b**: Testing manual

1. **Pantalla Home**: ¿Aparece proyecto reciente? ¿Botón "Nueva Tarea" funciona?
2. **Nueva Tarea**: ¿Se ve sin sidebar? ¿Botones "Ver propuesta" y "Cancelar" funcionan?
3. **Propuesta**: ¿Se ve sin sidebar? ¿Bloque tiene estructura fija (Modo | Modelo | Por qué)?
4. **Navegación**: ¿Breadcrumb refleja estado actual? ¿Back funciona?

---

## 3. QUÉ SE ELIMINA DE INMEDIATO

**Eliminaciones hard** (no refactorización):

1. **Todo el código de sidebar**:
   - `st.sidebar` completamente removido
   - Si existe `pwr/components/sidebar.py` → borrar
   - Todos los links de sidebar → borrar

2. **Navegación global via sidebar**:
   - No habrá radio button de "Home" / "Proyectos" / "Radar"
   - No habrá search box en sidebar
   - No habrá settings link en sidebar

3. **Estilos de sidebar**:
   - Si hay CSS para `.stSidebar` → remover
   - Si hay `st.set_page_config(layout="wide")` ajustar a layout normal

**Qué NO se elimina** (necesario aún):
- Router (funcionando)
- Database (intacta)
- Componentes de propuesta/resultado (refactorizar solo, no borrar)

---

## 4. QUÉ REEMPLAZA AL MENÚ LATERAL

### Header Superior (nuevo)

```
[Logo] PWR                    [Usuario] [Salir]
──────────────────────────────────────────────
Breadcrumb: PWR > Proyecto > Tarea > [Estado]
```

**Componente**: `pwr/components/header.py`
**Altura**: ~80px máximo
**Fijo**: Sí (siempre visible al scroll)

### Breadcrumb Sobrio

- Click en "Proyecto" → abre Proyecto
- Click en "Tarea" → vuelve a Propuesta (si pendiente)
- Estado actual → NO es clickeable (marca dónde estás)
- Sin decoración (flechas mínimas, colores discretos)

### Navegación Local (por pantalla)

Cada página tiene sus botones nativos:
- **Home**: Click en proyecto | "Nueva Tarea" input
- **Nueva Tarea**: "Ver propuesta" | "Cancelar"
- **Propuesta**: "Ejecutar" | (alternativas si usuario lo pide)
- **Resultado**: "Guardar" | "Mejorar" | "Nueva tarea" | "Proyecto"

No hay menú global. Cada estado tiene su flujo.

---

## 5. CÓMO SE EXPRESA ARRIBA LA JERARQUÍA DEL FLUJO

### Breadcrumb visual

```
PWR > Proyecto: Marketing 2026 > Tarea: Resumir análisis > [Propuesta]
```

**Lo que marca:**
- "Proyecto: Marketing 2026" = contexto superior (PROYECTO es primero)
- "Tarea: Resumir análisis" = unidad de trabajo
- "[Propuesta]" = estado actual (entre corchetes, no es clickeable)

### Orden en breadcrumb es SIEMPRE

```
PWR > [Proyecto] > [Tarea] > [Estado]
```

No se puede cambiar. Esto refuerza la jerarquía PROYECTO → Tarea.

### Cuando NO hay Proyecto (Home)

```
PWR
```

Solo el logo. Sin proyecto en breadcrumb = Home.

---

## 6. ACCIÓN PRINCIPAL POR ESTADO (en Hito A)

| Estado | Acción Principal | Botón | Visual |
|--------|-----------------|-------|--------|
| **Home** | Abrir proyecto O crear nueva tarea | Toggle: Proyectos \| Nueva Tarea | Dos secciones claras |
| **Nueva Tarea** | Escribir tarea + proyecto | "Ver propuesta" (protagonista) | Full screen, input grande |
| **Propuesta** | Ejecutar | "Ejecutar" (protagonista) | Bloque fijo, botón claro |

**Lo que NO hay en Hito A:**
- Modo/Modelo no son reales (vienen de Router, Hito B)
- Ejecutar no hace nada aún (es estructura)
- Resultado no aparece (Hito C)

---

## 7. EXPLÍCITAMENTE FUERA DE HITO A

**Queda para Hito B-E:**

- ❌ Router generando propuestas reales (Hito B)
- ❌ Ejecución real de tareas (Hito B)
- ❌ Persistencia de resultados (Hito C)
- ❌ Pantalla de Resultado (Hito C)
- ❌ Guardar como Asset (Hito C)
- ❌ "Mejorar análisis" / RACING mode (Hito E)
- ❌ Pantalla Proyecto / Historial (Hito C)
- ❌ Onboarding automático (Hito D)
- ❌ Radar / Analytics (Hito 6+)

**Hito A es SOLO estructura de navegación y layout.**

---

## 8. CÓMO VALIDAR SI HITO A MEJORA CLARIDAD

### Criterio 1: "Sin leer, el siguiente paso es evidente"

**Test**: Usuario abre Home. ¿Sin instrucciones, qué hace?
- ✅ Debería hacer click en "Nueva Tarea" O abrir un proyecto
- ❌ Si duda, intenta navegar con sidebar (que ya no existe)

**Cómo verificar**:
```
Paso 1: Usuario abre app
Paso 2: Pregunta: "¿Qué haces?"
Espera: Click en "Nueva Tarea" o proyecto, no busca sidebar
```

### Criterio 2: "Breadcrumb refuerza jerarquía"

**Test**: ¿En Nueva Tarea, el usuario ve que el proyecto es contexto superior?
- ✅ Breadcrumb muestra "Proyecto > Tarea"
- ❌ Si proyecto es al mismo nivel que tarea (o menos visible)

**Cómo verificar**:
```
Paso 1: Abre Nueva Tarea desde Home
Paso 2: Mira breadcrumb
Espera: "PWR > Proyecto: [nombre] > Tarea: [nuevo]"
```

### Criterio 3: "Sidebar desapareció, claridad aumentó"

**Test**: ¿Sin sidebar, hay menos visual noise?
- ✅ App se siente más limpia, menos "panel administrativo"
- ❌ Si aparecen menús escondidos o navegación confusa

**Cómo verificar**:
```
Paso 1: Captura pantalla de Home actual (con sidebar)
Paso 2: Captura pantalla de Home de Hito A (sin sidebar)
Paso 3: ¿Cuál se entiende más rápido?
```

### Criterio 4: "Cada estado tiene acción clara"

**Test**: ¿En cada pantalla, hay UNA acción protagonista?
- Home: "Nueva Tarea" o "Proyectos" (dos opciones, pero igual de visibles)
- Nueva Tarea: "Ver propuesta" (única opción principal)
- Propuesta: "Ejecutar" (única opción principal)

**Cómo verificar**:
```
Por cada pantalla:
- ¿Hay un botón más grande que otros?
- ¿La acción es obvia?
- ¿O el usuario se distrae con otras opciones?
```

### Criterio 5: "Usuario no se pierde en navegación"

**Test**: ¿El usuario puede volver a Home desde cualquier lugar?
- ✅ Click en "PWR" en breadcrumb vuelve a Home
- ✅ Click en "Cancelar" vuelve a Home
- ❌ Usuario queda atrapado en una pantalla

**Cómo verificar**:
```
Paso 1: Usuario en Nueva Tarea
Paso 2: Toca "Cancelar"
Espera: Vuelve a Home
```

---

## CHECKLIST DE IMPLEMENTACIÓN HITO A

**Día 1-2: Estructura**
- [ ] Eliminar sidebar completamente
- [ ] Crear header.py con logo + breadcrumb
- [ ] Crear breadcrumb.py helper
- [ ] Refactorizar app.py para usar header en cada página

**Día 2-3: Home**
- [ ] Mostrar proyectos recientes (DB query)
- [ ] Mostrar última tarea por proyecto (timestamp)
- [ ] Botón "Abrir" en cada proyecto
- [ ] Input "Nueva tarea" con botón "Crear"
- [ ] Sin sidebar, full width

**Día 3-4: Nueva Tarea**
- [ ] Full screen, sin sidebar
- [ ] Campos: Título, Descripción, Proyecto (selector)
- [ ] Botón "Ver propuesta" (protagonista)
- [ ] Botón "Cancelar" (secundario)
- [ ] Navegación: Click → propuesta state

**Día 4-5: Propuesta (estructura)**
- [ ] Mostrar resumen de tarea
- [ ] Bloque: Modo | Modelo | Por qué (hardcoded por ahora)
- [ ] Botón "Ejecutar" (protagonista)
- [ ] Sin lógica de Router (Hito B)
- [ ] Sin ejecución real (Hito B)

**Día 5-7: Validación**
- [ ] Testing manual: Home → Nueva Tarea → Propuesta
- [ ] Breadcrumb funciona en cada pantalla
- [ ] Botones "Cancelar" vuelven a Home
- [ ] Sin sidebar visible
- [ ] Header aparece en todas las pantallas
- [ ] Criterios de aceptación pasan (5 tests)

---

## STATUS TECH

### Objetivo Actual
Implementar estructura base de Hito A: eliminar sidebar, crear header, refactorizar flujo principal.

### Hecho ✅
- Propuesta de reestructuración aprobada
- Orden de implementación definido
- Criterios de validación claros

### En Progreso ⏳
- Microplan ejecutable (THIS DOCUMENT)

### Bloqueadores / Riesgos

| Riesgo | Probabilidad | Mitigación |
|--------|-------------|-----------|
| Usuario confundido post-cambio sidebar | Media | Hito D (onboarding) aclara flujo |
| Home con muchas queries (performance) | Media | Cachear últimos 5 proyectos en sesión |
| Breadcrumb rompe en mobile | Media | Versión compacta: "PWR / Proyecto / Tarea" |
| Proposal state sin Router todavía | Alta | Hardcodear propuesta; Router entra en Hito B |

### Siguiente Paso Recomendado

**Inmediato**:
1. Albert aprueba Hito A microplan (THIS)
2. Comenzamos Día 1 (Fase 1: Header + Eliminar Sidebar)

**Si Albert ajusta algo**:
- Especificar qué cambiar
- Re-validar 48h

**Post-aprobación**:
- Código: Comenzar eliminación de sidebar
- Testing: Al terminar cada Fase, validar contra criterios

### Decisión que necesita Albert

> **¿Aprobamos este microplan de Hito A?**
>
> ¿O hay ajustes en:
> - Orden de Fases?
> - Criterios de validación?
> - Estados que deben cambiar?
> - Scope (qué entra / qué no)?
>
> **Responde una sola vez. No iteramos microplan.**
> Si sí → Comenzamos en 2 horas.
> Si no → Qué cambios. Los hacemos y commiteamos.

---

**Documento cerrado. Microplan listo para ejecución.**

*Fecha: 2026-04-18 | Versión: 1.0 | Status: Pendiente aprobación para codificar*
