# BLOQUE H: Microplan de Implementación — Persistencia Visible

**Estado:** 🔴 NO IMPLEMENTAR AÚN — SOLO ESPECIFICACIÓN
**Requerimientos:** Aprobados con ajustes
**Objetivo:** PWR se sienta como workspace con memoria útil

---

## 1. ARCHIVOS A TOCAR

### Archivo principal: `app.py`

**Funciones a modificar:**

```
1. display_onboarding_result()
   - Línea aproximada: ~550-700 (dentro de helpers o en app)
   - Cambio: Añadir sección "Guardado en" compacta

2. home_view()
   - Línea aproximada: ~2090-2232
   - Cambio: Añadir sección "Hoy" antes de "Trabajo en progreso"

3. project_view()
   - Línea aproximada: ~2271+ (master-detail layout)
   - Cambio: Separar tareas ejecutadas vs pendientes en sidebar/main
```

### Archivos que NO tocan:

```
❌ router.py (cero cambios)
❌ BD schema (cero cambios, datos ya existen)
❌ ExecutionService
❌ helpers (excepto display_onboarding_result)
❌ new_task_view()
❌ onboarding_view() (ya modificado en G4)
```

---

## 2. QUÉ SE MOSTRARÁ EXACTAMENTE POST-RESULTADO

### Estructura visual (de arriba a abajo):

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  [RESULTADO DEL MODELO - ya existe, sin cambios]      │
│  "Aquí está tu respuesta..."                          │
│                                                         │
│  ─────────────────────────────────────────────────────│
│                                                         │
│  ✅ Guardado                                           │
│  En: Mi primer proyecto                              │
│  Tarea: Resume este documento                        │
│                                                         │
│  ─────────────────────────────────────────────────────│
│                                                         │
│  [CTA PRINCIPAL: 📂 Ver en proyecto]                 │
│                                                         │
│  Más acciones:                                        │
│  🔄 Reutilizar como contexto                         │
│  🎯 Crear tarea relacionada                          │
│  📋 Copiar resultado                                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Detalles de implementación:

#### Sección "Guardado" (después del resultado, antes de CTAs)

```python
# display_onboarding_result() añade:

st.divider()  # Separador ligero

col1, col2 = st.columns([0.15, 0.85])
with col1:
    st.markdown("✅")  # Check simple
with col2:
    st.markdown("**Guardado**")

# Contexto en captions
task_name = task.get("title", "Tarea")[:40]  # Truncar si es largo
project_name = onboard_data.get("project", {}).get("name", "proyecto")[:40]

st.caption(f"En: **{project_name}**")
st.caption(f"Tarea: **{task_name}**")

st.write("")  # Espaciado pequeño
```

#### CTA Primaria (Ver en proyecto)

```python
# Botón claro, prominent
if st.button("📂 Ver en proyecto", use_container_width=True, type="primary"):
    st.session_state["active_project_id"] = onboard_data["project_id"]
    st.session_state["view"] = "home"  # O project_view directamente si existe
    st.rerun()

st.write("")  # Espaciado
```

#### Acciones secundarias (less prominent)

```python
st.caption("Más acciones:")

col1, col2, col3 = st.columns(3, gap="small")

with col1:
    if st.button("🔄 Reutilizar", use_container_width=True):
        # Guardar resultado en session para pasar como contexto
        st.session_state["context_from_result"] = extract
        st.session_state["view"] = "new_task"
        st.rerun()

with col2:
    if st.button("🎯 Crear relacionada", use_container_width=True):
        # Crear task en proyecto actual basada en este resultado
        st.session_state["new_task_from_result"] = True
        st.session_state["view"] = "new_task"
        st.rerun()

with col3:
    if st.button("📋 Copiar", use_container_width=True):
        # Copiar al clipboard (Streamlit no tiene clipboard directo)
        # Alternativa: mostrar texto seleccionable
        with st.expander("Copiar resultado"):
            st.text_area("", value=extract, height=100, disabled=True)
```

**Jerarquía visual:**
- ✅ "Ver en proyecto" es PRIMARY (azul, grande)
- ✅ "Reutilizar" / "Crear relacionada" son secundarias (buttons normales)
- ✅ "Copiar" es más secundaria (menos importante)

**Cambio total en display_onboarding_result():** ~30 líneas nuevas

---

## 3. CÓMO QUEDARÁ LA SECCIÓN "Hmantén"

### Ubicación: Home, ANTES de "Trabajo en progreso"

### Estructura visual:

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│  ### 🏠 Mis tareas                                  │
│                                                      │
│  #### Hoy                                           │
│  ✅ Resume este documento                          │
│     Mi primer proyecto · hace 10 min                │
│  ✅ Escribe email                                   │
│     Mi primer proyecto · hace 1 hora                │
│                                                      │
│  [Línea divisor ligera]                            │
│                                                      │
│  #### Trabajo en progreso                          │
│  [Grid normal - sin cambios]                       │
│                                                      │
│  #### Mis proyectos                                │
│  [Grid normal - sin cambios]                       │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### Detalles de implementación:

#### Query: Traer tareas ejecutadas del día

```python
# home_view() añade (después de cargar recent_tasks):

from datetime import datetime, timedelta

# Traer tareas ejecutadas en últimas 24 horas
executed_today = []
for task in recent_tasks:
    task_updated = task.get("updated_at")
    if task_updated:
        task_date = datetime.fromisoformat(task_updated)
        if (datetime.now() - task_date) <= timedelta(hours=24):
            executed_today.append(task)

# Ordena por más reciente primero
executed_today.sort(key=lambda t: t.get("updated_at", ""), reverse=True)
```

#### Display: Sección "Hoy"

```python
if executed_today:
    st.markdown("#### Hoy")

    for task in executed_today[:5]:  # Máximo 5 tareas
        col1, col2 = st.columns([0.8, 0.2])

        with col1:
            st.markdown(f"✅ **{task['title'][:50]}**")

            project_name = task.get("project_name", "proyecto")[:30]
            time_ago = format_time_ago(task.get("updated_at", ""))

            st.caption(f"{project_name} · {time_ago}")

        with col2:
            if st.button("→ Abrir", key=f"hoy_{task['id']}", use_container_width=True):
                st.session_state["active_project_id"] = task["project_id"]
                st.session_state["selected_task_id"] = task["id"]
                st.rerun()

    st.divider()
```

**Características:**
- ✅ Compacta (2 líneas por tarea)
- ✅ Escaneable (proyecto + tiempo en caption)
- ✅ Botón "Abrir" directo a tarea
- ✅ Máximo 5 (no abruma)
- ✅ Usa timestamp existente en BD

**Cambio total en home_view():** ~25 líneas nuevas

---

## 4. CÓMO SE SEPARARÁN EJECUTADAS / PENDIENTES EN PROYECTO

### Ubicación: `project_view()`, en la sección de tareas

### Estructura visual:

```
┌──────────────────────────────────────────────────────┐
│  Proyecto: Mi primer proyecto                        │
│  (3 tareas, 2 ejecutadas)                           │
│                                                      │
│  #### Ejecutadas                                    │
│  ✅ Resume documento                                │
│     [Resultado disponible] · hace 30 min            │
│  ✅ Escribe email                                   │
│     [Resultado disponible] · hace 2 horas           │
│                                                      │
│  #### Pendientes                                    │
│  📌 Analiza gráfico                                 │
│                                                      │
│  [Nueva tarea en proyecto]                          │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### Detalles de implementación:

#### Query: Separar ejecutadas / pendientes

```python
# project_view() modifica la sección de tareas:

tasks = get_project_tasks(pid)

executed_tasks = [t for t in tasks if t.get("has_result")]  # Has execution result
pending_tasks = [t for t in tasks if not t.get("has_result")]
```

#### Display: Ejecutadas

```python
if executed_tasks:
    st.markdown("#### ✅ Ejecutadas")

    for task in executed_tasks:
        col1, col2 = st.columns([0.75, 0.25])

        with col1:
            st.markdown(f"✅ **{task['title'][:40]}**")

            time_ago = format_time_ago(task.get("updated_at", ""))
            st.caption(f"[Resultado disponible] · {time_ago}")

        with col2:
            if st.button("Abrir", key=f"exec_{task['id']}", use_container_width=True):
                st.session_state["selected_task_id"] = task["id"]
                st.rerun()

    st.write("")  # Espaciado
```

#### Display: Pendientes

```python
if pending_tasks:
    st.markdown("#### 📌 Pendientes")

    for task in pending_tasks:
        col1, col2 = st.columns([0.75, 0.25])

        with col1:
            st.markdown(f"📌 **{task['title'][:40]}**")

        with col2:
            if st.button("Ejecutar", key=f"pend_{task['id']}", use_container_width=True):
                st.session_state["selected_task_id"] = task["id"]
                st.session_state["view"] = "new_task"  # O task_detail_view
                st.rerun()

    st.write("")  # Espaciado
```

#### Display: Nueva tarea

```python
if st.button("➕ Nueva tarea en este proyecto", use_container_width=True):
    st.session_state["view"] = "new_task"
    st.session_state["active_project_id"] = pid
    st.rerun()
```

**Características:**
- ✅ Separación visual clara (#### headers)
- ✅ Badges de estado (✅, 📌)
- ✅ Compacta (una línea por tarea)
- ✅ "Resultado disponible" visible
- ✅ Botones accionables directos

**Cambio total en project_view():** ~40 líneas

---

## 5. ACCIONES FINALES CON JERARQUÍA (POST-RESULTADO)

### Orden visual (TOP to BOTTOM):

```
1. PRIMARIA (type="primary", full width, azul)
   📂 Ver en proyecto
   → Lleva a project_view o home+proyecto
   → User siente "vuelvo a donde pertenece esto"

2. SECUNDARIAS (buttons normales, 2 cols)
   🔄 Reutilizar como contexto
   → Guarda resultado en session_state
   → Abre new_task_view con contexto prefilled

   🎯 Crear tarea relacionada
   → Abre new_task_view en proyecto actual
   → Sugestión automática basada en resultado

3. MÁS SECUNDARIA (expandible, compacta)
   📋 Copiar resultado
   → Expander con texto seleccionable
   → No es CTA tan prominente
```

### Código exacto:

```python
# Post-resultado, después de sección "Guardado"

# ========== ACCIÓN PRIMARIA ==========
if st.button("📂 Ver en proyecto",
             use_container_width=True,
             type="primary",
             key="result_view_project"):
    st.session_state["active_project_id"] = onboard_data["project_id"]
    st.session_state["view"] = "home"
    st.rerun()

st.write("")

# ========== ACCIONES SECUNDARIAS ==========
col1, col2 = st.columns(2, gap="small")

with col1:
    if st.button("🔄 Reutilizar como contexto",
                 use_container_width=True,
                 key="result_reutilizar"):
        st.session_state["context_from_result"] = extract
        st.session_state["view"] = "new_task"
        st.rerun()

with col2:
    if st.button("🎯 Crear tarea relacionada",
                 use_container_width=True,
                 key="result_create_related"):
        st.session_state["new_task_from_result"] = task_id
        st.session_state["view"] = "new_task"
        st.rerun()

st.write("")

# ========== ACCIÓN TERCIARIA ==========
with st.expander("📋 Copiar resultado", expanded=False):
    st.text_area("",
                 value=extract,
                 height=150,
                 disabled=True,
                 label_visibility="collapsed")
    st.caption("Selecciona y copia el texto que necesites")
```

**Jerarquía visual:**
- ✅ Primaria: Grande, azul, full-width, clara intención
- ✅ Secundarias: 2 buttons iguales, menos peso visual
- ✅ Terciaria: Expander cerrado, no distrae

---

## 6. QUÉ NO TOCARÁS

```
❌ router.py
   → Decisiones eco/racing sin cambios
   → Complejidad del router intacta

❌ BD schema
   → Ya guarda has_result, updated_at
   → No nuevo columns
   → Query es sobre datos existentes

❌ ExecutionService
   → Execute logic sin cambios
   → Solo consume datos que ya genera

❌ onboarding_view()
   → Ya modificado en G4
   → Solo display_onboarding_result cambia

❌ new_task_view()
   → Mismo flujo
   → (Futuro) puede recibir context_from_result

❌ Radar
   → Sin cambios

❌ Autenticación
   → Sin cambios

❌ Multiusuario
   → Sin cambios
```

---

## 7. CÓMO VALIDARÍAS QUE PWR YA SE SIENTE COMO WORKSPACE

### Validación A: "¿Dónde quedó mi trabajo?"

```
Usuario ejecuta tarea en onboarding
Ve resultado
Se pregunta: ¿Dónde está?

✅ ÉXITO:
  - Sección "Guardado en:" visible
  - Dice proyecto nombre, tarea nombre
  - Usuario puede clicar "Ver en proyecto"
  - User siente "está seguro aquí"

❌ FALLO:
  - No hay señal de guardado
  - No sabe dónde encontrarlo
```

### Validación B: "¿Qué hice hoy?"

```
Usuario vuelve a Home días después
Se pregunta: ¿Qué hice?

✅ ÉXITO:
  - Sección "Hoy" visible
  - Muestra 2-3 tareas ejecutadas
  - Con timestamps ("hace 10 min", "hace 3 horas")
  - Proyecto de cada tarea claro
  - Puede abrir directamente

❌ FALLO:
  - No hay historial visible
  - Tiene que buscar en grids
  - Sin contexto temporal
```

### Validación C: "¿Dónde retomo?"

```
Usuario abre proyecto conocido
Se pregunta: ¿Qué está hecho, qué no?

✅ ÉXITO:
  - Sección "Ejecutadas" clara
  - Sección "Pendientes" clara
  - Badges de estado obvios (✅, 📌)
  - "Resultado disponible" para ejecutadas
  - Puede abrir cualquiera

❌ FALLO:
  - Lista plana, sin separación
  - No sé cuál se hizo
  - Sin contexto de estado
```

### Validación D: "¿Qué puedo hacer con el resultado?"

```
Usuario ve resultado ejecutado
Se pregunta: ¿Qué hago con esto?

✅ ÉXITO:
  - Botón principal claro (Ver en proyecto)
  - Dos acciones útiles (Reutilizar, Crear)
  - Copiar disponible pero no invasivo
  - Cada acción conecta con siguiente paso

❌ FALLO:
  - Muchos botones con mismo peso
  - No está claro cuál es siguiente paso
  - Copiar compite con acciones principales
```

### Validación E: "¿Es esto un workspace real?"

```
Pregunta abierta después de usar 20 minutos:

"Describe PWR con una palabra"

✅ ÉXITO (respuestas esperadas):
  - "Workspace"
  - "Espacio de trabajo"
  - "Herramienta con memoria"
  - "Proyecto con tareas"

❌ FALLO (respuestas que indican fallo):
  - "Demo"
  - "Tool aislada"
  - "Ejecutador de tareas"
  - "No sé si se guardó"
```

### Métrica final:

**80%+ usuarios responden positivamente en E → Bloque H ÉXITO**

---

## 8. STATUS TECH REAL

### Objetivo actual
```
Pasar de "herramienta aislada" a "workspace con memoria visible"
```

### Hecho (previo)
```
✅ G1-G4: Flujo principal limpio
✅ Sidebar dinámico: Dormido en flujos, despierto en navegación
✅ BD: Guarda tareas, resultados, proyectos
✅ ExecutionService: Genera datos necesarios
✅ has_result, updated_at: Ya existen en BD
```

### En progreso
```
🟡 Este microplan: Especificación de implementación
```

### Bloqueadores
```
🔴 NINGUNO: Todos los datos ya existen en BD
```

### Riesgos
```
⚠️ Muy bajo:
   - Solo cambios visuales
   - Datos ya existen
   - No toca backend
   - Queries simples sobre datos existentes
```

### Complejidad
```
🟢 Baja:
   - ~95 líneas nuevas total
   - 3 funciones modificadas
   - Cambios visuales, no arquitectura
```

### Siguientes pasos
```
1. Albert aprueba este microplan de implementación
2. Si hay feedback → ajustes concretos
3. Cuando listo → abrir implementación H1
   - display_onboarding_result() cambios
   - home_view() "Hoy" section
   - project_view() ejecutadas/pendientes
4. Validación en vivo (7 tests)
5. Ajustes post-validación si necesario
```

### Decisiones que necesita Albert
```
¿Apruebas este microplan de implementación?
¿Cambios en jerarquía de acciones?
¿Cambios en compacidad de "Hoy"?
¿Cuándo abro H1 para implementar?
```

---

## SÍNTESIS

**Bloque H de implementación** convierte PWR en workspace con memoria visible mediante:

1. ✅ Post-resultado: Sección "Guardado en" clara + acciones jerárquicas
2. ✅ Home: Sección "Hoy" compacta que muestra historial del día
3. ✅ Proyecto: Separación clara ejecutadas/pendientes
4. ✅ Acciones: Primaria (Ver en proyecto), secundarias (Reutilizar), terciaria (Copiar)

**Cambios totales:** ~95 líneas en 3 funciones
**Riesgo:** Muy bajo
**Complejidad:** Baja

---

**Listo para aprobación e implementación.**
