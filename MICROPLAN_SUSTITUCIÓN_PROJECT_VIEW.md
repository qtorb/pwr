# MICROPLAN: SUSTITUCIÓN PROGRESIVA DE project_view()

**Fecha**: 2026-04-18
**Estado**: 🔵 Esperando aprobación de Albert
**Alcance**: Reemplazar monolito legacy por flujo correcto
**Restricción**: Solo reemplazo, cero features nuevas

---

## RESPONSABILIDADES ACTUALES DE project_view() (700+ líneas)

```
project_view() ACTUAL (línea 2286-2700+):
├── 1. SIDEBAR (Captura + Lista)
│   ├── Renderiza nombre de proyecto
│   ├── Captura de nueva tarea (text_area)
│   ├── Preview de decisión del Router
│   ├── Contexto opcional
│   ├── Botón "Generar propuesta"
│   └── Lista de tareas separadas por estado (Ejecutadas vs Pendientes)
│
├── 2. MAIN (Ejecución + Resultado)
│   ├── Selecciona tarea según selected_task_id
│   ├── Valida que tarea pertenece a proyecto
│   ├── Renderiza botón "Ejecutar"
│   ├── Maneja flujo completo de ejecución
│   ├── Renderiza resultado (si existe)
│   ├── Maneja acciones post-ejecución
│   │   ├── "Guardar como activo"
│   │   ├── "Mejorar con análisis más profundo"
│   │   └── Panel de guardado de assets
│   └── Maneja flujo de mejora (iteración)
│
├── 3. STATE MANAGEMENT (Complejo)
│   ├── trace_key = múltiples ejecuciones
│   ├── save_panel_key (flujo de guardado)
│   ├── improve_in_progress_key (flujo de mejora)
│   ├── improved_result_key (resultado mejorado)
│   └── improved_trace_key (trazabilidad de mejora)
│
├── 4. EJECUCIÓN (ExecutionService)
│   ├── Inicializa ExecutionService en cada rerun
│   ├── Maneja 3 tipos de resultado (executed, preview, failed)
│   ├── Guarda en BD (router_metrics, llm_output, etc.)
│   ├── Muestra progreso visual
│   └── Maneja errores y fallbacks
│
├── 5. INTEGRACIÓN CON ROUTER
│   ├── Llama execution_service.decide() (propuesta)
│   ├── Llama execution_service.execute() (ejecución)
│   └── Maneja routing_decision + routing_metrics
│
└── 6. MANEJO DE ASSETS (Guardado de resultados)
    └── Panel de "Guardar como activo"
```

---

## 1️⃣ RESPONSABILIDADES QUE DESAPARECEN

**En la sustitución, project_view() deja de ser:**

| Responsabilidad | Desaparece porque | Trasladado a |
|---|---|---|
| **Captura de tarea (text_area)** | Duplica `new_task_view()` | `new_task_view()` |
| **Preview de decisión en sidebar** | Innecesario aquí | `proposal_view()` |
| **Botón "Generar propuesta"** | Flujo real es new_task → proposal | Router (main) |
| **Ejecución (botón Ejecutar)** | Responsabilidad de `result_view()` | `result_view()` |
| **Manejo de flujo de mejora** | Feature 2ª fase | Post-reemplazo |
| **Panel de "Guardar como activo"** | Feature 2ª fase | Post-reemplazo |
| **State management complejo** | Dispersado en keys huérfanas | Simplificado |
| **Inicialización de ExecutionService** | Cada vista maneja la suya | `proposal_view()` + `result_view()` |

**Resultado**: project_view() pasa de 700+ líneas a ~100 líneas (solo contenedor)

---

## 2️⃣ DISTRIBUCIÓN DE RESPONSABILIDADES EN VISTAS NUEVAS

### Vista A: `new_task_view()` (EXISTENTE - se reutiliza)

**Qué hace ahora**:
```python
# Línea ~2052
def new_task_view():
    # Input: Título, Descripción, Contexto opcional
    # Crear tarea en BD
    # Ir a proposal_view
```

**Qué hace en el flujo nuevo**:
```
ENTRADA: Desde project_view (sidebar) o desde Home (botón "Nueva tarea")
│
├─ Captura tarea (text_area)
├─ Contexto opcional (expander)
├─ Botón "Generar propuesta"
│
└─ SALIDA:
   └─ Crea tarea en BD
   └─ Cambia view = "proposal"
   └─ Establece selected_task_id
   └─ Rerun → main() enruta a proposal_view()
```

**Cambio necesario**: NINGUNO. Reutilización directa.

---

### Vista B: `proposal_view()` (EXISTENTE - se reutiliza)

**Qué hace ahora**:
```python
# Línea ~2140
def proposal_view():
    # Muestra decisión del Router (mode, model, reasoning)
    # Botón "Ejecutar"
    # Cambio a result_view
```

**Qué hace en el flujo nuevo**:
```
ENTRADA: Desde new_task_view (después de crear tarea)
│
├─ Muestra tarea capturada
├─ Llama decision_engine.decide(task_input)
├─ Muestra: Modo, Modelo, Motivo
├─ Botón "Ejecutar" (primario)
│
└─ SALIDA (cuando se ejecuta):
   └─ Cambia view = "result"
   └─ Rerun → main() enruta a result_view()
```

**Cambio necesario**: NINGUNO. Reutilización directa.

---

### Vista C: `result_view()` (EXISTENTE - se reutiliza)

**Qué hace ahora**:
```python
# Línea ~2055
def result_view():
    # Ejecuta tarea con execution_service.execute()
    # Muestra resultado
    # Guarda en BD
```

**Qué hace en el flujo nuevo**:
```
ENTRADA: Desde proposal_view (después de ejecutar)
│
├─ Ejecuta tarea
├─ Maneja 3 tipos de resultado (executed, preview, failed)
├─ Muestra resultado (text_area editable)
├─ Botón "Guardar como activo" (futuro feature, por ahora disabled)
├─ Botón "Mejorar análisis" (futuro feature, por ahora disabled)
│
└─ SALIDA:
   └─ El usuario cierra / abre otra tarea
   └─ Si cierra: vuelve a proyecto (sidebar)
   └─ Si abre otra: proposal_view con nueva tarea
```

**Cambio necesario**: Agregar botón "Volver a proyecto" o "Cerrar" que cambie view a "project"

---

## 3️⃣ PAPEL RESIDUAL DE "PROYECTO" COMO CONTENEDOR

### Nueva Estructura de project_view() (~100 líneas)

```python
def project_view():
    """
    NUEVO PAPEL: Contenedor que decide qué vista mostrar
    NO renderiza UI de ejecución, solo coordina.
    """

    # 1. VALIDACIÓN (línea 2292-2300)
    pid = st.session_state.get("active_project_id")
    if not pid:
        st.info("Selecciona un proyecto.")
        return

    project = get_project(pid)
    if not project:
        st.warning("No se pudo cargar el proyecto.")
        return

    # 2. HEADER COMPACTO (línea 2311-2321) - SE MANTIENE
    h1, h2 = st.columns([5.5, 1])
    with h1:
        st.markdown(f"... {project['name']}")
    with h2:
        if st.button("Cerrar"):
            st.session_state["active_project_id"] = None
            st.rerun()

    st.markdown("---")

    # 3. LAYOUT: Sidebar + Main (SE MANTIENE)
    sidebar, main = st.columns([0.25, 0.75], gap="large")

    # 4. SIDEBAR: SOLO LISTA + CAPTURA (SIMPLIFICADO)
    with sidebar:
        st.caption(f"Trabajando en: **{project['name']}**")

        # NUEVO: Router interno al sidebar
        sidebar_action = st.radio(
            "",
            ["Tareas", "Nueva tarea"],
            key=f"sidebar_action_{pid}",
            label_visibility="collapsed"
        )

        if sidebar_action == "Tareas":
            # Mostrar lista de tareas (existente, sin cambios)
            tasks = get_project_tasks(pid)
            st.markdown(f"### Tareas ({len(tasks)})")

            search = st.text_input("Buscar", key=f"search_{pid}", label_visibility="collapsed")
            filtered = get_project_tasks(pid, search=search)

            # Mostrar ejecutadas y pendientes (EXISTENTE)
            # ... (170 líneas actuales se mantienen sin cambios)
            for t in filtered:
                if st.button("Abrir", key=f"open_task_{t['id']}"):
                    st.session_state["selected_task_id"] = t["id"]
                    # ← AQUÍ VA LA LÓGICA DE DECISIÓN (ver punto 4️⃣)
                    st.rerun()

        elif sidebar_action == "Nueva tarea":
            # Redirige al flujo new_task_view
            st.session_state["view"] = "new_task"
            st.rerun()

    # 5. MAIN: Router interno (NUEVO)
    with main:
        tid = st.session_state.get("selected_task_id")

        if not tid:
            st.info("Selecciona o crea una tarea para trabajar.")
            return

        task = get_task(tid)
        if not task or task["project_id"] != pid:
            st.info("Selecciona una tarea válida del proyecto.")
            return

        # ← AQUÍ VA LA DECISIÓN SOBRE VISTA (ver punto 4️⃣)
        # Por ahora, redirige al flujo correcto
        determine_and_route_to_view(task, pid)
```

**Cambios de responsabilidad**:
- ✅ SE MANTIENE: Header, cierre de proyecto
- ✅ SE MANTIENE: Sidebar con lista de tareas (sin captura)
- ✅ SE ELIMINA: Captura de tarea en sidebar (→ new_task_view)
- ✅ SE ELIMINA: Ejecución de tarea (→ result_view)
- ✅ SE ELIMINA: State management complejo (→ cada vista maneja la suya)
- 🆕 SE AGREGA: Router interno que decide qué vista renderizar

---

## 4️⃣ LÓGICA DE DECISIÓN: ¿A QUÉ VISTA VA CADA TAREA?

### Decisión basada en Estado de la Tarea

```python
def determine_and_route_to_view(task, project_id):
    """
    Decide a qué vista ir según el estado actual de la tarea.

    Reglas:
    1. Sin ejecutar (sin llm_output) → proposal_view (con ejecución)
    2. Con ejecutar (con llm_output) → result_view (mostrar resultado)
    3. Con error previo → proposal_view (permitir reintentar)
    """

    # ESTADO 1: Tarea sin ejecutar
    if not task.get("llm_output"):
        # Usuario abre tarea sin resultado
        # Debe entrar al flujo de ejecución
        st.session_state["view"] = "proposal"
        st.rerun()

    # ESTADO 2: Tarea con resultado
    elif task.get("llm_output"):
        # Usuario abre tarea con resultado
        # Debe ver el resultado
        st.session_state["view"] = "result"
        st.rerun()

    # ESTADO 3: Tarea con error (execution_status = "failed")
    elif task.get("execution_status") == "failed":
        # Usuario puede reintentar
        st.session_state["view"] = "proposal"
        st.rerun()
```

### Tabla de Decisión

| Estado de Tarea | llm_output | execution_status | → View | Razón |
|---|---|---|---|---|
| Nueva (sin usar) | None | None | proposal | Ejecutar por primera vez |
| Con resultado | "..." | "executed" | result | Mostrar resultado |
| Con demo (no ejecutada) | "[PROPUESTA...]" | "preview" | result | Mostrar propuesta previa |
| Con error | "" | "failed" | proposal | Permitir reintentar |

---

## 5️⃣ CÓDIGO LEGACY QUE QUEDA TEMPORALMENTE VIVO

### Fase 1 (Implementación): Dual-mode

**project_view() NUEVA coexiste con código legacy mientras se valida:**

```python
# MANTENER TEMPORALMENTE (hasta validación):

✅ MANTENER:
├── get_project() - Lee proyecto de BD
├── get_project_tasks() - Lee tareas de proyecto
├── Renderizado de sidebar (lista de tareas)
├── get_task() - Lee tarea específica
├── Validaciones básicas (task["project_id"] == pid)
└── Botón "Cerrar proyecto"

❌ NO MANTENER (eliminar inmediatamente):
├── Captura de tarea en sidebar (text_area, línea 2337-2343)
├── Preview de decisión en sidebar (línea 2359-2363)
├── Botón "Generar propuesta" (línea 2381-2385)
├── Contexto opcional en sidebar (línea 2367-2376)
├── MAIN section completo (ejecución, línea 2441-2700)
│   ├── Botón "Ejecutar"
│   ├── ExecutionService
│   ├── Flujo de ejecución (150+ líneas)
│   ├── Guardado de resultados
│   ├── Flujos de mejora
│   └── Panel "Guardar como activo"
├── Todas las claves de state complejas (trace_key, improve_in_progress_key, etc.)
└── Inicialización de ExecutionService en project_view
```

---

## 6️⃣ QUÉ SE ELIMINA DESPUÉS DE VALIDAR

**Después de que los 3 flujos funcionen sin depender de project_view():**

```
FASE 2 (Post-validación): Cleanup

ELIMINAR:
├── Línea 2337-2343: text_area de captura (duplicado con new_task)
├── Línea 2345-2363: Preview de decisión (duplicado con proposal)
├── Línea 2381-2385: Botón "Generar propuesta"
├── Línea 2367-2376: Contexto opcional (duplicado con new_task)
├── Línea 2441-2700: Sección MAIN completa (ejecución)
│   ├── execute_btn, ExecutionService, resultado, etc.
│   ├── trace_key, save_panel_key, improve_in_progress_key
│   └── Flujo de ejecución + guardado
├── Línea 2303-2304: Inicialización de ExecutionService
└── Línea 2306-2309: Lectura de docs/assets (si no se usan)

RESULTADO FINAL:
project_view() = ~100 líneas
├── Validación
├── Header
├── Sidebar (lista + botón "Nueva tarea")
└── Router a new_task/proposal/result
```

---

## 7️⃣ VALIDACIÓN: CÓMO PROBAR QUE NO DEPENDE DEL LEGACY

### Test 1: Captura de Tarea
```
Flujo: Home → "Nueva tarea" → new_task_view
├─ ¿Se abre new_task_view?
├─ ¿Captura la tarea correctamente?
├─ ¿Crea en BD?
└─ ¿Entra a proposal_view?

Resultado esperado: ✅ Funciona SIN usar project_view
```

### Test 2: Propuesta
```
Flujo: new_task_view → proposal_view
├─ ¿Se muestra la decisión del Router?
├─ ¿Se llama decision_engine.decide()?
├─ ¿Se renderiza modo, modelo, motivo?
└─ ¿Botón "Ejecutar" funciona?

Resultado esperado: ✅ Funciona SIN usar project_view
```

### Test 3: Ejecución
```
Flujo: proposal_view → result_view
├─ ¿Se ejecuta la tarea?
├─ ¿Se guarda en BD (llm_output)?
├─ ¿Se muestra el resultado?
└─ ¿El botón "Volver a proyecto" funciona?

Resultado esperado: ✅ Funciona SIN usar project_view
```

### Test 4: Desde project_view (Sidebar)
```
Flujo: project_view (sidebar) → Abrir tarea existente
├─ ¿selected_task_id se establece?
├─ ¿determine_and_route_to_view() decide correctamente?
├─ ¿Si sin ejecutar → proposal_view?
├─ ¿Si con resultado → result_view?
└─ ¿Botón "Cerrar" vuelve a Home?

Resultado esperado: ✅ Funciona CON project_view pero DELEGANDO
```

### Test 5: Crear Proyecto desde Home
```
Flujo: Home → "Crear proyecto" → abre nuevo → sidebar
├─ ¿Se crea en BD?
├─ ¿Se abre project_view?
├─ ¿Sidebar muestra "Sin tareas"?
└─ ¿Botón "Nueva tarea" funciona?

Resultado esperado: ✅ Funciona SIN usar captura en sidebar
```

---

## 📋 CHECKLIST DE VALIDACIÓN

```
VALIDACIÓN DE SUSTITUCIÓN:

[ ] Captura de tarea
    [ ] Funciona desde Home "Nueva tarea"
    [ ] Funciona desde project_view (radio "Nueva tarea")
    [ ] Crea en BD
    [ ] Entra a proposal_view correctamente

[ ] Propuesta
    [ ] Muestra decisión del Router
    [ ] Botón "Ejecutar" funciona
    [ ] Entra a result_view

[ ] Resultado
    [ ] Muestra llm_output
    [ ] Botón "Volver a proyecto" funciona
    [ ] Sin dependencia de project_view legacy

[ ] Flujo desde project_view (sidebar)
    [ ] Abrir tarea → determine_and_route_to_view decide correctamente
    [ ] Sin ejecutar → proposal_view
    [ ] Con resultado → result_view
    [ ] Cerrar proyecto → Home

[ ] Edge cases
    [ ] Tarea de otro proyecto (validación)
    [ ] Proyecto sin tareas (muestra mensaje)
    [ ] Error en ejecución (permite reintentar)
    [ ] Búsqueda en lista de tareas (sigue funcionando)

[ ] No hay regresiones
    [ ] Home sigue funcionando (Abrir, Crear, Continuar)
    [ ] new_task_view sigue funcionando
    [ ] proposal_view sigue funcionando
    [ ] result_view sigue funcionando
    [ ] Radar sigue funcionando

VALIDACIÓN FINAL: ¿Puedo eliminar todo el código legacy sin breakage?
```

---

## 📊 RESUMEN ARQUITECTÓNICO

### ANTES (project_view = monolito)
```
project_view() (700+ líneas)
├── Captura
├── Preview
├── Ejecución
├── Resultado
├── Mejora
└── Assets
```

### DESPUÉS (project_view = contenedor)
```
project_view() (100 líneas)
├── Header + Sidebar
├── Router → new_task_view()
├── Router → proposal_view()
├── Router → result_view()
└── Botón "Cerrar"

new_task_view()    (Captura)
proposal_view()    (Propuesta)
result_view()      (Ejecución + Resultado)
```

---

## 🔵 ESTADO: ESPERANDO APROBACIÓN

**Este microplan:**
- ✅ Define exactamente qué se reemplaza
- ✅ No añade features nuevas
- ✅ Reutiliza código que ya funciona
- ✅ Mantiene UX similar
- ✅ Elimina monolito de forma progresiva
- ✅ Define validación clara

**Decisión requerida de Albert:**
1. ¿Apruebas este plan de sustitución?
2. ¿Algún cambio en la lógica de decisión (punto 4️⃣)?
3. ¿Alguna responsabilidad que deba mantenerse en project_view()?
4. ¿Orden preferido de implementación?

**Una vez aprobado:** Implementaré en fases:
- Fase 1: Router en project_view() + determine_and_route_to_view()
- Fase 2: Validación de los 3 flujos
- Fase 3: Cleanup del código legacy
