# PLAN: HOME V2 REFINADA

**Estado**: 🔵 Esperando aprobación para implementar
**Alcance**: Home como workspace de rendimiento (NO archivo)
**Restricción**: Solo UX refinada, cero features nuevas

---

## ESTRUCTURA HOME V2 (Nueva)

```
┌──────────────────────────────────────────────────────────┐
│                    HEADER PERSISTENTE                     │
│  [PWR]              [➕ Crear nuevo activo]  [⚙️ Settings] │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ SECCIÓN 1: CONTINUAR (Hero Block - Driver Principal)     │
│                                                          │
│  [📌 Tarea/Activo Principal]                            │
│  Título largo con contexto                              │
│  Proyecto: X | 3 líneas de resumen                      │
│                                                          │
│  [Badge: "Listo para pulir" / "Falta tu revisión"]     │
│  [Continuar →]                                          │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ SECCIÓN 2: ACTIVOS RECIENTES (Workspace)                │
│                                                          │
│ Últimas 5-6 cosas que creaste/ejecutaste                │
│                                                          │
│ [Informe]        [Email]         [Análisis]            │
│  Título           Título          Título                │
│  Proyecto · Hace 2h Proyecto · Hace 1h Proyecto · Hoy  │
│                                                          │
│ Cada activo:                                            │
│  - Tipo visible (icono + label)                         │
│  - Título                                               │
│  - Preview corto (50 chars)                             │
│  - Proyecto + tiempo                                    │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ SECCIÓN 3: PROYECTOS RELEVANTES (4-6 máximo)           │
│                                                          │
│ Proyectos (4 activos / 12 en archivo)                   │
│                                                          │
│ [📁 Proyecto A]        [📁 Proyecto B]                 │
│  3 tareas | Retomar    2 tareas | Retomar             │
│                                                          │
│ [📁 Proyecto C]        [📁 Proyecto D]                 │
│  5 tareas | Retomar    1 tarea | Retomar              │
│                                                          │
│ Micro-acción "Retomar": Abre proyecto + tarea más     │
│ relevante (sin hacer click en "Abrir")                 │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ SECCIÓN 4: HOY (Opcional, si hay ejecuciones)          │
│                                                          │
│ ✅ Tarea ejecutada hoy 1                                │
│ ✅ Tarea ejecutada hoy 2                                │
│ ✅ Tarea ejecutada hoy 3                                │
│                                                          │
│ (Sección colapsable o discreta)                        │
└──────────────────────────────────────────────────────────┘
```

---

## CAMBIOS CONCRETOS EN app.py

### 1. CTA PERSISTENTE EN HEADER (NUEVO)

**Ubicación**: Dentro de `render_header_minimal()` o crear sección nueva

```python
# NUEVA SECCIÓN - Antes de render_header_minimal()

def render_home_header_with_cta():
    """
    Header con CTA persistente: "Crear nuevo activo"
    Debe ser visible sin scroll, se siente "fuera" del flujo.
    """
    col1, col2, col3 = st.columns([1, 4, 1])

    with col1:
        st.markdown(f"<div style='font-size:18px; font-weight:700;'>PWR</div>", unsafe_allow_html=True)

    with col2:
        # Botón persistente - PRIMARIO
        if st.button("➕ Crear nuevo activo", use_container_width=True, key="header_cta_create", type="primary"):
            st.session_state["view"] = "new_task"
            st.rerun()

    with col3:
        if st.button("⚙️", key="header_settings", use_container_width=False):
            st.session_state["show_settings"] = True
            st.rerun()

    st.divider()
```

---

### 2. BLOQUE CONTINUAR (MODIFICADO - Hero)

**Ubicación**: Línea 2150 de home_view()

**Antes**:
```python
st.markdown("### 🏠 Mis tareas")
```

**Después**:
```python
# ==================== SECCIÓN 1: CONTINUAR (DRIVER PRINCIPAL) ====================

# Obtener la tarea más relevante para continuar
def get_most_relevant_task():
    """
    Obtiene la tarea más relevante para continuar.
    Criterios: tarea ejecutada, proyecto activo, hace poco.
    """
    with get_conn() as conn:
        cursor = conn.execute("""
            SELECT
                t.id,
                t.title,
                t.project_id,
                p.name AS project_name,
                t.llm_output,
                t.updated_at,
                t.execution_status
            FROM tasks t
            LEFT JOIN projects p ON p.id = t.project_id
            WHERE t.llm_output IS NOT NULL
              AND TRIM(t.llm_output) != ''
            ORDER BY t.updated_at DESC
            LIMIT 1
        """)
        result = cursor.fetchone()
        return dict(result) if result else None

# Renderizar bloque continuar
most_relevant = get_most_relevant_task()

if most_relevant:
    st.markdown("#### Continuar desde aquí")

    # Hero block: Grande, prominente
    col_main = st.columns(1)[0]
    with col_main:
        with st.container(border=True):
            col_title, col_action = st.columns([0.85, 0.15])

            with col_title:
                st.markdown(f"**📌 {most_relevant['title'][:80]}**")
                st.caption(f"{most_relevant['project_name']} • {format_time_ago(most_relevant['updated_at'])}")

                # Preview corto del resultado
                preview = most_relevant['llm_output'][:180].replace('\n', ' ')
                st.caption(f"__{preview}...__")

                # Badge semántico (NUEVO)
                badge_text = determine_semantic_badge(most_relevant)
                st.markdown(f"<span style='background-color:#E0E7FF; padding:2px 8px; border-radius:4px; font-size:11px; color:#4338CA;'>{badge_text}</span>", unsafe_allow_html=True)

            with col_action:
                st.write("")  # Espaciado
                if st.button("Continuar →", key=f"hero_continue_{most_relevant['id']}", use_container_width=True, type="primary"):
                    st.session_state["active_project_id"] = most_relevant["project_id"]
                    st.session_state["selected_task_id"] = most_relevant["id"]
                    st.session_state["view"] = "project"
                    st.rerun()

st.divider()
```

---

### 3. BADGES SEMÁNTICOS (NUEVA FUNCIÓN)

```python
def determine_semantic_badge(task):
    """
    Determina un badge semántico que responde:
    "¿Por qué debería abrir esto ahora?"

    NO usar estados técnicos (En curso, Done, Waiting).
    SI usar lenguaje útil y humano.
    """
    status = task.get('execution_status', '')
    updated_at = task.get('updated_at', '')

    # Lógica simple por ahora
    # En Fase 2 puede incluir más heurística

    if status == 'preview':
        return "✨ Propuesta pendiente de revisar"
    elif status == 'executed':
        # Si hace menos de 1 hora
        if is_recent(updated_at, hours=1):
            return "🔥 Recién ejecutado"
        elif is_recent(updated_at, days=1):
            return "✅ Listo para pulir"
        else:
            return "📋 Disponible para retomar"
    else:
        return "📌 En progreso"

def is_recent(timestamp, hours=None, days=None):
    """Helper: ¿Es reciente?"""
    from datetime import datetime, timedelta

    if not timestamp:
        return False

    try:
        task_time = datetime.fromisoformat(timestamp)
        now = datetime.now(task_time.tzinfo) if task_time.tzinfo else datetime.now()

        if hours:
            delta = timedelta(hours=hours)
        elif days:
            delta = timedelta(days=days)
        else:
            return False

        return (now - task_time) <= delta
    except:
        return False
```

---

### 4. ACTIVOS RECIENTES (MODIFICADO - Morphología)

**Ubicación**: Después del bloque Continuar

```python
# ==================== SECCIÓN 2: ACTIVOS RECIENTES ====================

st.markdown("#### Últimos activos")

recent_tasks = get_recent_executed_tasks(limit=6)

if not recent_tasks:
    st.caption("📋 Sin activos aún. Captura una para comenzar.")
else:
    # Mostrar en grilla 3 por fila
    cols_per_row = 3
    for i in range(0, len(recent_tasks), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, task in enumerate(recent_tasks[i:i+cols_per_row]):
            with cols[j]:
                with st.container(border=True):
                    # TIPO visible (NEW)
                    asset_type = infer_asset_type(task)
                    st.markdown(f"<span style='font-size:10px; color:#6B7280;'>{asset_type}</span>", unsafe_allow_html=True)

                    # TÍTULO
                    st.markdown(f"**{task['title'][:45]}**")

                    # PREVIEW (NEW)
                    preview = task.get('llm_output', '')[:80].replace('\n', ' ')
                    if preview:
                        st.caption(f"_{preview}..._")

                    # PROYECTO + TIEMPO
                    st.caption(f"{task['project_name']} · {format_time_ago(task['updated_at'])}")

                    # ACCIÓN
                    if st.button("Abrir", key=f"asset_open_{task['id']}", use_container_width=True):
                        st.session_state["active_project_id"] = task["project_id"]
                        st.session_state["selected_task_id"] = task["id"]
                        st.session_state["view"] = "project"
                        st.rerun()

st.divider()
```

---

### 5. FUNCIÓN: INFER_ASSET_TYPE

```python
def infer_asset_type(task):
    """
    Infiere el tipo de activo (informe, email, análisis, tabla, etc.)
    basándose en el contenido o metadatos.

    Por ahora: heurística simple
    En Fase 2: puede usar metadata explícita en BD
    """
    output = task.get('llm_output', '').lower()
    title = task.get('title', '').lower()

    # Patrones simples
    if any(word in output for word in ['tabla', 'csv', 'excel', '| ']):
        return "📊 Tabla"
    elif any(word in output for word in ['email', 'asunto', 'para:', 'de:']):
        return "✉️ Email"
    elif any(word in output for word in ['análisis', 'conclusión', 'resultado']):
        return "🔍 Análisis"
    elif any(word in output for word in ['plan', 'estrategia', 'propuesta']):
        return "📋 Plan"
    elif any(word in output for word in ['código', 'def ', 'function']):
        return "💻 Código"
    else:
        return "📄 Documento"
```

---

### 6. PROYECTOS RELEVANTES (MODIFICADO)

**Ubicación**: Línea 2218

```python
# ==================== SECCIÓN 3: PROYECTOS RELEVANTES ====================

st.markdown("#### Proyectos")

all_projects = get_projects()
projects_with_activity = get_projects_with_activity()

# Mostrar solo 4-6 más relevantes
relevant_projects = projects_with_activity[:6]

# Indicador de archivo
total_projects = len(all_projects)
shown_projects = len(relevant_projects)
if total_projects > shown_projects:
    st.caption(f"Mostrando lo más relevante ahora ({shown_projects} / {total_projects} en archivo)")
else:
    st.caption(f"Todos tus proyectos ({shown_projects})")

st.write("")

if not relevant_projects:
    st.caption("📁 Sin proyectos. Crea uno para comenzar.")
else:
    cols_per_row = 2
    for i in range(0, len(relevant_projects), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, project in enumerate(relevant_projects[i:i+cols_per_row]):
            with cols[j]:
                with st.container(border=True):
                    st.markdown(f"**📁 {project['name'][:35]}**")
                    st.caption(f"{project['active_task_count']} tareas")

                    # MICRO-ACCIÓN (NEW): Retomar
                    most_recent_task = get_most_recent_task_in_project(project['id'])

                    col_open, col_retomar = st.columns([0.5, 0.5])

                    with col_open:
                        if st.button("Abrir", key=f"home_open_project_{project['id']}", use_container_width=True):
                            st.session_state["active_project_id"] = project["id"]
                            st.session_state["selected_task_id"] = None
                            st.session_state["view"] = "project"
                            st.rerun()

                    with col_retomar:
                        if most_recent_task:
                            if st.button(f"Retomar", key=f"home_retomar_{most_recent_task['id']}", use_container_width=True):
                                st.session_state["active_project_id"] = project["id"]
                                st.session_state["selected_task_id"] = most_recent_task["id"]
                                st.session_state["view"] = "project"
                                st.rerun()
                        else:
                            st.button("Sin tareas", key=f"home_notasks_{project['id']}", disabled=True, use_container_width=True)

# Enlace a archivo completo (si hay más proyectos)
if total_projects > shown_projects:
    if st.button("Ver archivo completo →", key="view_all_projects", use_container_width=True):
        st.session_state["show_all_projects"] = True
        st.rerun()
```

---

### 7. FUNCIÓN: GET_MOST_RECENT_TASK_IN_PROJECT

```python
def get_most_recent_task_in_project(project_id):
    """
    Obtiene la tarea más reciente (con resultado) en un proyecto.
    Sirve para la micro-acción "Retomar".
    """
    with get_conn() as conn:
        cursor = conn.execute("""
            SELECT
                id,
                title,
                updated_at
            FROM tasks
            WHERE project_id = ?
              AND llm_output IS NOT NULL
              AND TRIM(llm_output) != ''
            ORDER BY updated_at DESC
            LIMIT 1
        """, (project_id,))
        result = cursor.fetchone()
        return dict(result) if result else None
```

---

### 8. SECCIÓN HOY (OPCIONAL)

```python
# ==================== SECCIÓN 4 (OPCIONAL): HOY ====================

st.markdown("#### Hoy")

today_tasks = []
with get_conn() as conn:
    cursor = conn.execute("""
        SELECT
            t.id,
            t.title,
            t.project_id,
            p.name AS project_name,
            t.updated_at
        FROM tasks t
        LEFT JOIN projects p ON p.id = t.project_id
        WHERE date(t.updated_at) = date('now', 'localtime')
          AND t.llm_output IS NOT NULL
          AND TRIM(t.llm_output) != ''
        ORDER BY t.updated_at DESC
        LIMIT 5
    """)
    today_tasks = [dict(row) for row in cursor.fetchall()]

if not today_tasks:
    st.caption("📋 Sin ejecuciones hoy")
else:
    with st.expander("Ver últimas ejecuciones", expanded=False):
        for task in today_tasks:
            time_ago = format_time_ago(task.get("updated_at", ""))
            col1, col2 = st.columns([0.85, 0.15])
            with col1:
                st.markdown(f"✅ **{task['title'][:45]}**")
                project_name = task.get('project_name') or "Sin proyecto"
                st.caption(f"{project_name} · {time_ago}")
            with col2:
                if st.button("→", key=f"home_today_{task['id']}", help="Abrir", use_container_width=True):
                    st.session_state["active_project_id"] = task["project_id"]
                    st.session_state["selected_task_id"] = task["id"]
                    st.session_state["view"] = "project"
                    st.rerun()
```

---

## ORDEN DE CAMBIOS EN home_view()

1. **Nuevo**: Agregar `render_home_header_with_cta()` al inicio (ANTES de home_view)
2. **Modificar**: Reemplazar sección "Mis tareas" por "Continuar desde aquí" (hero block)
3. **Nuevo**: Agregar funciones helper (badges, asset_type, get_most_recent_task)
4. **Modificar**: Sección "Trabajo en progreso" → "Últimos activos" con morphología
5. **Modificar**: Sección "Mis proyectos" → Mostrar solo 6 relevantes + indicador archivo
6. **Nuevo**: Agregar micro-acción "Retomar" en tarjetas de proyecto
7. **Modificar**: Botones CTA en footer (si hay espacio)
8. **Opcional**: Colapsar sección "Hoy" en expander

---

## CRITERIOS DE ACEPTACIÓN (Albert)

✅ **¿Se entiende como workspace y no como archivo?**
   - Bloque "Continuar" es prominente y hero
   - Proyectos limitados a 6 (no lista larga)
   - Copy dice "lo más relevante"

✅ **¿El CTA principal está visible sin scroll?**
   - `render_home_header_with_cta()` en header persistente
   - Botón "Crear nuevo activo" siempre visible

✅ **¿El bloque "Continuar" da una razón clara para volver?**
   - Badge semántico responde "¿por qué abrir?"
   - No usa estados técnicos
   - Ejemplo: "Listo para pulir", "Falta tu revisión"

✅ **¿Activos y proyectos se distinguen visualmente?**
   - Activos: tipo visible (📊 Tabla, ✉️ Email, etc.)
   - Activos: preview del contenido
   - Proyectos: solo nombre + conteo + acciones
   - Visual diferente (contenedor, spacing)

✅ **¿El usuario siente que no ha perdido los proyectos no visibles?**
   - Indicador: "4 / 12 en archivo"
   - Enlace: "Ver archivo completo →"
   - Copy tranquilizador: "Mostrando lo más relevante"

---

## ESTADO: ESPERANDO APROBACIÓN

**Decisiones pendientes:**
1. ¿El orden de secciones te parece correcto? (Continuar → Activos → Proyectos → Hoy)
2. ¿El badge semántico debe incluir más lógica ahora o esperar Fase 2?
3. ¿La micro-acción "Retomar" debe ser visible o estar en un menú contextual?
4. ¿Debo mantener los botones "Nueva tarea" y "Crear proyecto" abajo o eliminarlos?

**Una vez aprobado**: Implementación inmediata en app.py.
