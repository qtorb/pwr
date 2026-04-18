# VALIDACIÓN ARQUITECTÓNICA DE FLUJOS HOME → PROJECT

**Fecha**: 2026-04-18
**Método**: Análisis de código + trazabilidad de estado
**Alcance**: 3 flujos + arquitectura de project_view()

---

## PARTE 1: VALIDACIÓN DE LOS 3 FLUJOS ARREGLADOS

### Test 1: Abrir Proyecto (Varios proyectos)

#### Flujo Esperado
```
Home (selecciona proyecto A)
  ↓ [Abrir proyecto] → session_state = {active_project_id: A, selected_task_id: None, view: "project"}
  ↓ main() routing: elif current_view == "project": project_view()
  ↓ project_view():
      1. pid = st.session_state.get("active_project_id")  // ✅ A
      2. project = get_project(pid)  // ✅ Lee A de BD
      3. tasks = get_project_tasks(pid)  // ✅ Lee tareas de A
      4. Sidebar: lista tareas de A
      5. Main: selected_task_id = None → "Selecciona o crea una tarea..."
      6. ✅ CORRECTO: No arrastra tarea previa
```

#### Arquitectura de Estado
```python
# ANTES (Home - bugueado):
st.session_state["active_project_id"] = A
st.rerun()
# → main() ejecuta home_view() (sigue en home)

# AHORA (Home - arreglado):
st.session_state["active_project_id"] = A
st.session_state["selected_task_id"] = None  # ← Limpia cualquier tarea previa
st.session_state["view"] = "project"          # ← Routing explícito
st.rerun()
# → main() ejecuta project_view() (entra a proyecto)
```

#### Validación Técnica: ✅ PASA
- ✅ active_project_id se establece correctamente
- ✅ selected_task_id se limpia a None
- ✅ view se cambia a "project"
- ✅ Routing explícito en main() (línea 3483-3484)
- ✅ project_view() valida: `if task["project_id"] != pid: st.info("Selecciona una tarea válida")`
- **Resultado**: Abre proyecto sin tarea preseleccionada ✅

---

### Test 2: Crear Proyecto Nuevo

#### Flujo Esperado
```
Home (crea proyecto nuevo)
  ↓ [Crear proyecto] → form submit
  ↓ pid = create_project(...) // ✅ Inserta en BD, retorna ID nuevo
  ↓ session_state = {active_project_id: pid_nuevo, selected_task_id: None, view: "project"}
  ↓ main() routing: elif current_view == "project": project_view()
  ↓ project_view():
      1. pid = st.session_state.get("active_project_id")  // ✅ pid_nuevo
      2. project = get_project(pid_nuevo)  // ✅ Lee de BD
      3. tasks = get_project_tasks(pid_nuevo)  // ✅ Lista vacía (nuevo proyecto)
      4. Sidebar: "Sin tareas en este proyecto"
      5. Main: "Selecciona o crea una tarea..."
      6. ✅ CORRECTO: Abre proyecto nuevo vacío
```

#### Arquitectura de Estado (línea 2278-2283)
```python
pid = create_project(name, description, objective, base_context, base_instructions, tags, files)
st.session_state["active_project_id"] = pid           # ← Nuevo proyecto
st.session_state["selected_task_id"] = None           # ← Limpia estado
st.session_state["show_create_project"] = False       # ← Cierra modal
st.session_state["view"] = "project"                  # ← Routing explícito
st.rerun()
```

#### Validación Técnica: ✅ PASA
- ✅ create_project() inserta en BD y retorna ID
- ✅ active_project_id se establece al nuevo ID
- ✅ selected_task_id se limpia a None
- ✅ show_create_project se cierra (modal desaparece)
- ✅ view se cambia a "project"
- ✅ Routing explícito en main()
- ✅ project_view() carga proyecto nuevo sin tareas previas
- **Resultado**: Nuevo proyecto aparece en Home + se abre automáticamente ✅

---

### Test 3: Continuar Tarea desde Home

#### Flujo Esperado
```
Home (tarea activa con resultado)
  ↓ [Continuar] → session_state = {active_project_id: P, selected_task_id: T, view: "project"}
  ↓ main() routing: elif current_view == "project": project_view()
  ↓ project_view():
      1. pid = P  // ✅ Proyecto correcto
      2. project = get_project(P)  // ✅ Carga proyecto
      3. Sidebar: lista tareas de P (destaca tarea T)
      4. Main: selected_task_id = T
          → task = get_task(T)
          → Valida: task["project_id"] == pid  // ✅ Coinciden
          → Muestra resultado de T
      5. ✅ CORRECTO: Entra a tarea correcta en proyecto correcto
```

#### Arquitectura de Estado (línea 2210-2214)
```python
if st.button("Continuar", ...):
    st.session_state["active_project_id"] = task["project_id"]  # ← Proyecto
    st.session_state["selected_task_id"] = task["id"]           # ← Tarea
    st.session_state["view"] = "project"                        # ← Routing explícito
    st.rerun()
```

#### Validación Técnica: ✅ PASA
- ✅ active_project_id = proyecto de la tarea
- ✅ selected_task_id = ID de tarea (NO None)
- ✅ view = "project"
- ✅ Routing explícito en main()
- ✅ project_view() valida: `if task["project_id"] != pid:` (línea 2449)
- ✅ Entra a tarea correcta con su proyecto correcto
- **Resultado**: Abre tarea en el proyecto correcto ✅

---

## PARTE 2: ANÁLISIS DE FRAGILIDAD DE `project_view()`

### 🔴 PUNTOS FRÁGILES IDENTIFICADOS

#### 1. **Mezcla de Responsabilidades (CRÍTICO)**

La función `project_view()` hace TODO:
- Renderiza UI (sidebar + main)
- Gestiona estado de sesión (trace_key, execute_btn, etc.)
- Llama a ExecutionService
- Maneja 3 tipos de resultado (executed, preview, failed)
- Guarda en BD
- Maneja flujos de mejora y guardado de assets

**Síntoma**: Si algo falla en cualquier paso, toda la vista se quiebra.

**Ejemplo**:
```python
# Línea 2303-2304: Cada rerun crea ExecutionService nuevo
with get_conn() as conn:
    execution_service = ExecutionService(conn)

# Línea 2489: Si execution_service.execute() falla, no hay fallback limpio
result = execution_service.execute(task_input)
```

---

#### 2. **State Management Complejo (ALTO RIESGO)**

**Múltiples claves de session_state para un solo flujo:**
```python
# Línea 2453
trace_key = f"trace_{tid}"

# Línea 2645-2648
save_panel_key = f"save_asset_panel_{tid}"
improve_in_progress_key = f"improve_in_progress_{tid}"
improved_result_key = f"improved_result_{tid}"
improved_trace_key = f"improved_trace_{tid}"

# Línea 2601-2613
st.session_state[trace_key] = { ... }  # Guarda trazabilidad compleja
```

**Problema**: Si una tarea se ejecuta múltiples veces, los trace_keys se acumulan. Si se cambia `selected_task_id` rápidamente, los keys anteriores quedan huérfanos.

**Síntoma**: Comportamiento inconsistente al alternar entre tareas.

---

#### 3. **Validación de Proyecto/Tarea Débil (MEDIO)**

```python
# Línea 2448-2451
task = get_task(tid)
if not task or task["project_id"] != pid:
    st.info("Selecciona una tarea válida del proyecto.")
    return
```

**Problema**: La validación es correcta, pero:
- Se ejecuta DESPUÉS de leer selected_task_id
- Si selected_task_id tiene un ID de tarea de otro proyecto, muestra solo `st.info()`
- No hay logging de quién/cuándo intentó acceder a tarea inválida

---

#### 4. **Inicialización de ExecutionService sin Caché (BAJO)**

```python
# Línea 2303-2304: Se crea en CADA rerun
with get_conn() as conn:
    execution_service = ExecutionService(conn)
```

**Problema**: ExecutionService es pesado (carga ModelCatalog, DecisionEngine, etc.). En cada rerun se reinicializa.

**Impacto**: Latencia innecesaria.

---

#### 5. **Búsqueda de Tareas Sin Límite (BAJO-MEDIO)**

```python
# Línea 2392-2393
search = st.text_input("Buscar", ...)
filtered = get_project_tasks(pid, search=search)
```

**Problema**: Si proyecto tiene 1000+ tareas y búsqueda retorna todas, el sidebar se vuelve lento.

---

#### 6. **Lógica de Ejecución Entrelazada (ALTO RIESGO)**

```python
# Línea 2472: if execute_btn ejecuta lógica compleja dentro
if execute_btn:
    # ... 150+ líneas de lógica de ejecución, manejo de errores, BD, UI
    # Si algo falla a mitad, el estado queda inconsistente
```

**Problema**: La ejecución tiene muchos puntos de fallo pero sin transacciones claras.

---

### 📊 RESUMEN DE FRAGILIDAD

| Aspecto | Severidad | Descripción |
|---------|-----------|-------------|
| Mezcla de responsabilidades | 🔴 CRÍTICO | Una función hace UI + lógica + BD + estado |
| State management | 🔴 CRÍTICO | Múltiples keys, se acumulan, pueden quedar huérfanos |
| Validación débil | 🟡 MEDIO | Existe pero es mínima, sin logging |
| ExecutionService sin caché | 🟠 BAJO | Se reinicializa en cada rerun |
| Búsqueda sin límite | 🟠 BAJO | Puede ser lenta con muchas tareas |
| Flujo de ejecución monolítico | 🔴 CRÍTICO | 150+ líneas sin separación clara |

---

## PARTE 3: ESTADO ACTUAL DE LOS 3 FLUJOS

### Después de los Fixes de Home

| Operación | Estado Inicial | Luego de Fix | Flujo Resultante | Status |
|-----------|---|---|---|---|
| **Abrir proyecto** | Quedaba en Home | Entra a project_view | Proyecto sin tarea | ✅ OK |
| **Crear proyecto** | Quedaba en Home | Entra a project_view | Proyecto nuevo vacío | ✅ OK |
| **Continuar tarea** | Quedaba en Home | Entra a project_view | Tarea en proyecto | ✅ OK |

---

## PARTE 4: RECOMENDACIÓN DEL SIGUIENTE PASO

### El Dilema

**Situación actual:**
- Home está funcional (fixes implementados ✅)
- project_view() es el destino, pero tiene arquitectura frágil
- Hay 2 caminos divergentes

### Opción A: Seguir Arreglando Bugs en project_view()
**Pros:**
- Menos disruptivo
- Puedes iterar rápido

**Contras:**
- Aumenta technical debt
- Cada fix toca más de lo necesario
- Riesgo de regresiones

---

### Opción B: Rediseñar project_view()
**Pros:**
- Limpia separación de responsabilidades
- Mejor mantenibilidad
- Menos bugs a largo plazo

**Contras:**
- Más trabajo inmediato
- Riesgo de romper flujos mientras cambias

---

### Opción C: Reemplazar Definitivamente el Flujo Legacy
**Pros:**
- Clean slate
- Oportunidad de usar 3-pantallas reales (new_task → proposal → result)
- No cargo técnico

**Contras:**
- Cambio arquitectónico grande
- Requiere replantear sidebar + main

---

## RECOMENDACIÓN FINAL: OPCIÓN C (Reemplazar)

### Por Qué

1. **Ya tienes la arquitectura**: new_task → proposal → result están funcionando
2. **project_view() es legacy**: Mezcla 6 intenciones en una función
3. **Home ya funciona**: Los flujos de Home abren proyecto_view(), pero ese destino es frágil
4. **Momentum**: Los fixes de Home just se completaron, el sistema está limpio

### Plan Arquitectónico (Fase siguiente)

```
FASE ACTUAL (Hito resuelto):
  Home: Abrir / Crear / Continuar → project_view() ✅

FASE SIGUIENTE (recomendado):
  Home: Abrir proyecto → Sidebar limpio (SIN main, sin tareas)
  Home: Crear proyecto → Mismo comportamiento
  Home: Continuar tarea → Entra a new_task o proposal (dependiendo de estado)

ESTRUCTURA NUEVA:
  project_view() → Se divide en:
    1. sidebar_project() — Panel de contexto + lista de tareas
    2. main_task_selector() — Router a new_task/proposal/result según estado
    3. Eliminan mezcla de responsabilidades
```

### Riesgo vs. Beneficio

| Aspecto | Arreglar Bugs | Rediseñar | Reemplazar |
|---------|--|--|--|
| Tiempo inmediato | ⚡ Rápido | ⏱️ Medio | ⏳ Más tiempo |
| Deuda técnica | ⬆️ Sube | ➡️ Igual | ⬇️ Baja |
| Mantenibilidad | ❌ Peor | ✅ Mejor | ✅ Mejor |
| Riesgos | 📌 Bajo | 📌 Medio | 📌 Medio |
| **Recomendación** | ❌ No | ⚠️ Quizás | ✅ SÍ |

---

## CONCLUSIÓN

**Los 3 flujos de Home funcionan correctamente después de los fixes.**

**project_view() sigue siendo el punto débil arquitectónico** porque:
- Mezcla responsabilidades (UI + lógica + BD + estado)
- State management complejo con múltiples keys
- Flujo de ejecución monolítico sin separación clara

**Recomendación: Reemplazar project_view() por arquitectura más limpia** que use los componentes que ya funcionan (new_task → proposal → result) en lugar de recrear la rueda con una función legacy.

**Siguiente paso a validar con Albert**: ¿Vamos por rediseño limpio o seguimos arreglando el legacy?
