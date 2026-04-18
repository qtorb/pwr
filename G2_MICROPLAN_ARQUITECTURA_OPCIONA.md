# G2: Separación clara de estados — MICROPLAN Opción A

## DECISIÓN APROBADA

Refactor arquitectura de home_view() en tres vistas limpias por estado de uso:
- **ESTADO A:** Onboarding (sin actividad previa)
- **ESTADO B:** Nueva tarea (captura limpia)
- **ESTADO C:** Home de trabajo (navegación + historial)

---

## 1. ARCHIVOS A TOCAR

### app.py (único archivo a modificar)

| Sección | Acción | Líneas aprox |
|---------|--------|--------------|
| **Función `main()`** | Agregar routing para new_task_view | 3113-3123 |
| **Función `home_view()`** | Simplificar para ESTADO C puro | 1868-2241 |
| **Nueva función `new_task_view()`** | Crear ESTADO B | (nueva) |
| **Nueva función `onboarding_view()`** | Extraer ESTADO A de home | (nueva) |
| **Mantener** | No tocar router, BD, ExecutionService | — |

---

## 2. QUÉ SE MUEVE: home_view() → onboarding_view() + new_task_view()

### ESTADO A: `onboarding_view()` (NUEVA FUNCIÓN)

**Origen:** Actual home_view() cuando `not has_activity` (líneas 1883-2087)

**Contenido:**
```
[1] Título: "🚀 Portable Work Router"

[2] Explicación 3-puntos:
    - Trabajar con más claridad
    - Entender por qué
    - Guardar y reutilizar

[3] Tabs: Home | Radar
    - Tab Home:
      [4] Ejemplos one-click (Resume, Escribe, Analiza)
      [5] Input: "¿Cuál es tu tarea?" (90px)
      [6] Decision preview
      [7] Botón "✨ Empezar"
      [8] Resultado (si está listo) con 3 bloques
      [9] 3 CTAs: Otra tarea | Copiar | Crear proyecto
      [10] Radar link discreta
    - Tab Radar: radar_view()

[11] Divider + micro-guía
```

**Función:** Completamente ESTADO A (onboarding puro)

**Session state que usa:**
- `onboard_capture_input` (input pre-llenado)
- `onboard_result_ready` (resultado listo?)
- `onboard_result` (task + result data)

---

### ESTADO B: `new_task_view()` (NUEVA FUNCIÓN)

**Origen:** Extraer de actual home_view() líneas 2105-2159 (input + decision + botón)

**Contenido:**
```
[1] Header: "← Volver" | "📁 Proyecto activo"

[2] Input: "¿Qué necesitas hacer ahora?" (90px)

[3] Decision preview

[4] Optional expander: "Añadir contexto (opcional)"

[5] Botón: "✨ Generar propuesta"

[6] Resultado (si está listo) con 3 bloques
```

**Función:** ESTADO B puro - captura de nueva tarea sin distracciones

**Session state que usa:**
- `home_capture_input` (input de nueva tarea)
- `home_task_context` (contexto opcional)
- `selected_task_id` (si se ejecuta)

**Diferencia clave vs actual:**
- ❌ NO aparece "Retoma tu trabajo"
- ❌ NO aparece "Tus proyectos"
- ✅ Aparece botón "← Volver" que limpia y vuelve a home (ESTADO C)

---

### ESTADO C: home_view() SIMPLIFICADO

**Origen:** Actual home_view() líneas 2089-2241

**Contenido:**

**Si `not has_activity`:**
```
→ Llamar onboarding_view() (ESTADO A)
```

**Si `has_activity`:**
```
[1] Header: "🏠 Mis tareas"

[2] Sección: "Trabajo en progreso"
    Grid de recent_tasks con botón "Continuar"

[3] Divider

[4] Sección: "Mis proyectos"
    Grid de projects con botón "Abrir"
    Botón "Crear proyecto"

[5] Botones de acción:
    [➕ Nueva tarea]
    [➕ Crear proyecto]
```

**Función:** ESTADO C puro - navegación de trabajo sin input arriba

**QUÉ DESAPARECE:**
- ❌ Input "¿Qué necesitas hacer ahora?" (se va a new_task_view)
- ❌ Decision preview (se va a new_task_view)
- ❌ Botón "Generar propuesta" (se va a new_task_view)
- ❌ Expander "Añadir contexto" (se va a new_task_view)

---

## 3. CÓMO QUEDARÍA main() CON ENRUTADO POR session_state

### Flujo actual (líneas 3113-3123):

```python
if current_view == "radar":
    radar_view()
elif st.session_state.get("active_project_id"):
    render_header()
    st.write("")
    project_view()
else:
    home_view()
```

### Flujo NEW (Opción A):

```python
current_view = st.session_state.get("view", "home")

if current_view == "radar":
    radar_view()

elif current_view == "new_task":
    # ESTADO B: Nueva tarea (pantalla dedicada)
    new_task_view()

elif st.session_state.get("active_project_id"):
    # Proyecto abierto (ya existe)
    render_header()
    st.write("")
    project_view()

else:
    # ESTADO C o A dependiendo de has_activity
    home_view()
```

### Cambio mínimo: agregar una condición antes de project_view()

---

## 4. TRANSICIONES DE ESTADO: Cómo se navega

### ESTADO A → ESTADO C:

```python
# En onboarding_view(), cuando user clickea "✨ Empezar"
st.session_state["onboard_result_ready"] = True
st.rerun()
# home_view() se llama, ve has_activity=True, salta a ESTADO C
```

### ESTADO C → ESTADO B:

```python
# En home_view(), botón "➕ Nueva tarea"
st.session_state["view"] = "new_task"
st.rerun()
# main() ve view="new_task" → llama new_task_view()
```

### ESTADO B → ESTADO C:

```python
# En new_task_view(), botón "← Volver"
st.session_state["view"] = "home"
st.session_state["home_capture_input"] = ""  # Limpia input
st.rerun()
# main() llama home_view() de nuevo
```

### ESTADO B → project_view():

```python
# En new_task_view(), cuando user clickea "✨ Generar propuesta"
st.session_state["selected_task_id"] = task_id
# home_view() en project_view() abierto, navega allá
st.rerun()
```

### ESTADO C → project_view():

```python
# En home_view(), cuando user clickea "Continuar" o "Abrir"
st.session_state["active_project_id"] = project_id
st.session_state["selected_task_id"] = task_id  # (si aplica)
st.rerun()
# main() ve active_project_id → llama project_view()
```

---

## 5. QUÉ SE REUTILIZA TAL CUAL

### Funciones que NO cambian:

| Función | Razón | Líneas |
|---------|-------|--------|
| `display_decision_preview()` | Se usa igual en new_task_view | 1552-1596 |
| `display_onboarding_result()` | Se usa igual en onboarding_view | 1598-1661 |
| `project_view()` | Completamente independiente | 2244+ |
| `radar_view()` | Completamente independiente | 1654-1866 |
| `ExecutionService` | Lógica de router sin cambios | router.py |
| Base de datos | Schema + queries igual | BD |
| Sidebar + project_selector | Funciona igual | main() + sidebar |

---

## 6. QUÉ NO TOCARÁS

### Off-limits (NUNCA modificar):

| Elemento | Por qué |
|----------|---------|
| **router.py** | Lógica de decisión independiente |
| **BD schema** | Estructura ya estable |
| **ExecutionService** | Ejecución sin cambios |
| **project_view()** | Ya funciona bien |
| **radar_view()** | Completamente separado |
| **Sidebar** | Navegación principal OK |
| **CSS/inyecciones** | Mantener igual |

---

## 7. MICROPLAN TÉCNICO DE MOVIMIENTO

### Paso 1: Crear `onboarding_view()` (nueva función)

**Origen:** Copiar home_view() líneas 1883-2087

**Cambios internos:**
- Renombrar variables locales si necesario (evitar conflictos con new_task_view)
- Lógica de `onboard_result_ready` idéntica
- Estructura de tabs, input, ejemplos idéntica

**No tocar:**
- display_decision_preview()
- display_onboarding_result()

---

### Paso 2: Crear `new_task_view()` (nueva función)

**Origen:** Extraer home_view() líneas 2105-2159

**Contenido:**
```python
def new_task_view():
    """
    ESTADO B: Nueva tarea limpia
    - Input para capturar tarea
    - Decision preview
    - Botón Generar propuesta
    - Sin "Retoma tu trabajo" ni "Tus proyectos"
    """

    # Header con botón Volver
    col1, col2 = st.columns([0.7, 0.3])
    with col1:
        st.markdown("### ¿Qué necesitas hacer ahora?")
    with col2:
        if st.button("← Volver", key="new_task_back"):
            st.session_state["view"] = "home"
            st.session_state["home_capture_input"] = ""
            st.rerun()

    st.write("")

    # Input (copia de home_view 2108-2116)
    capture_title = st.text_area(...)
    st.caption("Voy a elegir la mejor forma de resolverlo por ti")

    st.write("")

    # Decision preview (copia de home_view 2121-2134)
    if capture_title.strip():
        task_input = TaskInput(...)
        decision = execution_service.decision_engine.decide(task_input)
        display_decision_preview(decision, capture_title)

    st.write("")

    # Contexto opcional (copia de home_view 2138-2147)
    with st.expander("Añadir contexto (opcional)"):
        context = st.text_area(...)

    st.write("")

    # Botón Generar propuesta (copia de home_view 2151-2158)
    if st.button("✨ Generar propuesta", ...):
        # Crear tarea + ejecutar
        # (lógica actual de home_view)
        st.session_state["selected_task_id"] = task_id
        st.rerun()
```

**No tocar:**
- ExecutionService (inicializar igual)
- create_task, save_execution_result (usar igual)

---

### Paso 3: Simplificar `home_view()`

**Sacar:** Líneas 1883-2087 (ESTADO A onboarding)
→ Mover a onboarding_view()

**Sacar:** Líneas 2105-2159 (input para nueva tarea)
→ Mover a new_task_view()

**Quedar:** Líneas 2162-2241 (Retoma + Proyectos)

**Nuevo contenido simplificado:**
```python
def home_view():
    """
    ESTADO A + ESTADO C:
    - Si no hay actividad → onboarding_view()
    - Si hay actividad → grid de tareas + proyectos
    """

    recent_tasks = get_recent_executed_tasks(limit=1)
    projects = get_projects()
    has_activity = len(recent_tasks) > 0 or len(projects) > 0

    if not has_activity:
        onboarding_view()  # ESTADO A
        return

    # ESTADO C: Solo navegación
    st.markdown("### 🏠 Mis tareas")

    st.write("")

    # Trabajo en progreso (copia de líneas 2162-2183)
    st.markdown("#### Trabajo en progreso")
    recent_tasks = get_recent_executed_tasks(limit=5)
    if not recent_tasks:
        st.caption("Sin tareas ejecutadas")
    else:
        # Grid de tareas con botón "Continuar"
        ...

    st.divider()

    # Mis proyectos (copia de líneas 2186-2212)
    st.markdown("#### Mis proyectos")
    projects_with_activity = get_projects_with_activity()
    if not projects_with_activity:
        st.caption("Sin proyectos")
    else:
        # Grid de proyectos con botón "Abrir"
        ...

    st.write("")
    st.divider()

    # Botones de acción
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Nueva tarea", use_container_width=True, key="home_new_task"):
            st.session_state["view"] = "new_task"
            st.rerun()

    with col2:
        if st.button("➕ Crear proyecto", use_container_width=True, key="home_create_project"):
            st.session_state["show_create_project"] = True
            st.rerun()

    # Modal crear proyecto (copiar tal cual)
    if st.session_state.get("show_create_project"):
        ...
```

---

### Paso 4: Actualizar `main()`

**Cambio:** Agregar condición para new_task_view()

```python
def main():
    # ... (lineas 3076-3112 sin cambios)

    # ==================== ROUTING ====================
    current_view = st.session_state.get("view", "home")

    if current_view == "radar":
        radar_view()
    elif current_view == "new_task":  # ← NUEVA CONDICIÓN
        new_task_view()
    elif st.session_state.get("active_project_id"):
        render_header()
        st.write("")
        project_view()
    else:
        home_view()
```

---

## 8. VALIDACIÓN: CÓMO PROBARÍAS QUE QUEDÓ CLARO

### Test 1: ESTADO A (Onboarding nuevo)

**Setup:** Sin proyectos, sin tareas

**Test:**
```
Usuario entra
→ Ve explicación + ejemplos + input
→ Llena input y ve decision preview
→ Clickea "✨ Empezar"
→ Ve resultado con 3 bloques
→ Clickea "🚀 Otra tarea rápida"
→ Vuelve a input limpio (SIN ver "Retoma" ni "Proyectos")
```

**Observable:**
- ✅ No hay confusión: pantalla es SOLO onboarding
- ✅ Usuario entiende qué hacer sin pensar
- ✅ Resultado se ve sin scroll

---

### Test 2: ESTADO C (Home con actividad)

**Setup:** Tiene tareas y proyectos

**Test:**
```
Usuario entra a Home
→ Ve "Trabajo en progreso" (tareas recientes)
→ Ve "Mis proyectos"
→ NO ve input "¿Qué necesitas hacer ahora?" en Home
→ Clickea botón "➕ Nueva tarea"
→ Ve pantalla limpia con SOLO input (ESTADO B)
→ Clickea "← Volver"
→ Vuelve a Home con tareas + proyectos
```

**Observable:**
- ✅ Distinción clara: Home ≠ New task
- ✅ User no se confunde: ¿lleno input o clickeo tarea?
- ✅ Botón "Nueva tarea" es obvia como acción
- ✅ Volver funciona limpiamente

---

### Test 3: ESTADO B (Nueva tarea)

**Test:**
```
User clickea "➕ Nueva tarea" en Home
→ Ve input + decision preview + botón (nada más)
→ NO ve "Retoma tu trabajo"
→ NO ve "Tus proyectos"
→ Llena input
→ Clickea "✨ Generar propuesta"
→ Navega a project_view() (o resultado inline si lo dejamos)
```

**Observable:**
- ✅ Pantalla es LIMPIA (sin distracciones)
- ✅ Objetivo claro: capturar una tarea
- ✅ No hay opciones competidoras

---

### Test 4: Pregunta directa al usuario (después de cada estado)

**Después de Home:**
> "¿Cuál es tu próximo paso?"
- ✅ "Quiero hacer algo nuevo" → "Clico Nueva tarea"
- ✅ "Quiero retomar algo" → "Clico en la tarea"
- ✅ "Quiero entrar a un proyecto" → "Clico en proyecto"

**Después de New task:**
> "¿Qué ves en pantalla?"
- ✅ "Solo lo que necesito: escribir y ejecutar"
- ❌ "Muchas opciones, no sé qué hacer"

---

### Test 5: No-confusing signals

**Verificar:**
- ✅ Home no tiene input "¿Qué necesitas?" visible (va a new_task_view)
- ✅ New_task_view no tiene "Retoma tu trabajo" (va a home_view)
- ✅ Onboarding no tiene "Tus proyectos" (puro nuevo)
- ✅ Botones de navegación entre estados funcionan sin scroll
- ✅ Responsive: mobile y desktop se sienten claros

---

## 9. CRONOGRAMA DE IMPLEMENTACIÓN

### Fase 1: Estructura base (más corto)
1. Crear `onboarding_view()` (copiar de home)
2. Crear `new_task_view()` (extraer de home)
3. Simplificar `home_view()`
4. Actualizar `main()` con routing

**Tiempo estimado:** 45-60 min

### Fase 2: Validación + ajustes (rápida)
1. Test de estados A/B/C
2. Microajustes de copy/posición si salen
3. Validación de transiciones

**Tiempo estimado:** 20-30 min

---

## STATUS TECH REAL

| Aspecto | Estado | Detalles |
|---------|--------|----------|
| **Análisis** | ✅ Completado | Tres funciones identificadas, movimiento claro |
| **Rutas session_state** | ✅ Definidas | view="home"\|"new_task"\|"radar" + active_project_id |
| **Cambios necesarios** | ✅ Mapeados | app.py solo, 4 puntos de modificación |
| **Backend** | ✅ Sin cambios | router.py, BD, ExecutionService intactos |
| **Reutilización** | ✅ Máxima | display_* functions, helpers, ejecutores igual |
| **Riesgos** | ⚠️ Bajo | Solo refactor UI, lógica no cambia |
| **Validación** | ✅ Definida | 5 tests claros, observable directo |

---

## DECISIÓN QUE NECESITO

**¿Apruebo este microplan?**

1. **Sí, exacto así** → Procedo a implementar Opción A
2. **Ajustes en el movimiento** → Dime qué cambiar
3. **Cambio de enfoque** → Querés algo diferente

Mi recomendación: **Sí, exacto así.** El microplan es limpio, el riesgo es bajo, la validación es clara.

Cuando apruebes, empiezo implementación.

---

**FIN DE MICROPLAN G2 — OPCIÓN A**
