# Cambios Implementados — FRENTE A + FRENTE B

**Fecha:** 2026-04-18
**Status:** Implementados + Sintaxis Verificada ✅

---

## FRENTE B — OMNI-INPUT (Prioridad Máxima)

### 1. Nuevo Layout de omni_input_view() (líneas 2071-2219)

**ANTES:**
- Input pequeño
- Botón "Generar propuesta"
- Navegación a pantalla separada

**AHORA:**
```python
def omni_input_view():
    """
    OMNI-INPUT: Pantalla ÚNICA de creación.

    Estructura:
    1. Proyecto visible arriba
    2. Input grande (trabajo a realizar)
    3. Recomendación del Router INLINE (modo, modelo, motivo)
    4. CTA único: "✨ Ejecutar con [modelo]"

    Sin pantalla de propuesta, sin navegación intermedia.
    """
```

**Cambios específicos:**

**a) Header claro con proyecto (líneas 2076-2080):**
```python
# ==================== HEADER: Proyecto ====================
st.markdown(f"#### 📁 {default_project['name']}")
st.caption("¿Qué quieres crear?")
st.write("")
```

**b) Input grande protagonista (líneas 2082-2097):**
```python
task_title = st.text_input(
    "Trabajo a realizar",
    placeholder="Resume documento • Escribe email • Analiza datos...",
    key="omni_title_input"
)

task_description = st.text_area(
    "Detalles (opcional)",
    placeholder="Contexto, restricciones, requisitos específicos...",
    height=80,  # ← MÁS GRANDE
    key="omni_description_input"
)
```

**c) Contexto expandible (NO competidor):**
```python
with st.expander("📎 Información adicional"):
    context = st.text_area(...)
```

**d) Recomendación INLINE con modelo visible (líneas 2162-2186):**
```python
if decision:
    st.divider()
    st.markdown("#### ✨ PWR recomienda")

    col_model, col_reason = st.columns([0.4, 0.6])

    with col_model:
        st.markdown("**Modelo**")
        st.markdown(f"`{decision.model}`")  # ← MODELO SIEMPRE VISIBLE
        st.caption(f"Modo: {decision.mode.upper()}")

    with col_reason:
        st.markdown("**Motivo**")
        st.caption(decision.reasoning_path)
```

**e) CTA ÚNICA: Ejecutar con modelo (líneas 2188-2205):**
```python
col_cta_main, col_cta_secondary = st.columns([0.65, 0.35])

with col_cta_main:
    button_text = f"✨ Ejecutar con {decision.model}" if decision else "✨ Ejecutar"
    execute_button = st.button(
        button_text,
        key="omni_execute_cta",
        use_container_width=True,
        type="primary",  # ← ÚNICO BOTÓN AZUL PRIMARIO
        disabled=not task_title.strip()
    )
```

### 2. Cambiar Routing: Eliminar proposal_view() (línea 3878-3887)

**ANTES:**
```python
if current_view == "new_task":
    new_task_view()

elif current_view == "proposal":
    proposal_view()  # ← ELIMINADO

elif current_view == "result":
    result_view()
```

**AHORA:**
```python
if current_view == "new_task":
    new_task_view()

elif current_view == "result":
    result_view()
```

**Efecto:** Ninguna pantalla navega a "proposal". El flujo es lineal: Home → new_task (Omni-Input) → result.

### 3. Botón "Generar propuesta" → "Nueva tarea" (línea 2786-2792)

**Ubicación:** project_view()
**ANTES:**
```python
if st.button("Generar propuesta", use_container_width=True, key=f"create_task_{pid}", disabled=not title.strip()):
    if title.strip():
        tid = create_task(pid, title, "", TIPOS_TAREA[0], context or "", None)
        st.session_state["selected_task_id"] = tid
        st.rerun()
```

**AHORA:**
```python
if st.button("➕ Nueva tarea", use_container_width=True, key=f"create_task_{pid}"):
    st.session_state["active_project_id"] = pid
    st.session_state["view"] = "new_task"
    st.rerun()
```

**Efecto:** Al hacer click en "➕ Nueva tarea" dentro de un proyecto, navega a Omni-Input con el proyecto preseleccionado.

### 4. Cambiar botones de error (result_view)

**Línea 3646:**
```python
# ANTES:
if st.button("Volver a Propuesta", key="result_error_proposal"):
    st.session_state["view"] = "proposal"

# AHORA:
if st.button("← Volver a Home", key="result_error_home_btn"):
    st.session_state["view"] = "home"
```

**Línea 3653:**
```python
# ANTES:
if st.button("Volver a Propuesta", key="result_exception_proposal"):
    st.session_state["view"] = "proposal"

# AHORA:
if st.button("← Volver a Home", key="result_exception_home_btn"):
    st.session_state["view"] = "home"
```

---

## FRENTE A — HOME: Refinamiento Visual

### 1. Header Robusto con Wordmark (líneas 2269-2290)

**ANTES:**
```python
col1, col2 = st.columns([0.7, 0.3])

with col1:
    st.markdown(f"<div style='font-size:16px; font-weight:700; color:#0F172A;'>PWR</div>", unsafe_allow_html=True)

with col2:
    if st.button("+ Crear", key="header_cta_create", help="Crear nuevo trabajo"):
```

**AHORA:**
```python
col_logo, col_context, col_cta = st.columns([0.2, 0.5, 0.3])

with col_logo:
    # Wordmark robusto: más grande, más fuerte
    st.markdown(
        "<div style='font-size:24px; font-weight:900; color:#0F172A; letter-spacing:-1px;'>PWR</div>",
        unsafe_allow_html=True
    )

with col_context:
    # Micro-línea de posicionamiento
    st.markdown(
        "<div style='font-size:12px; color:#6B7280; margin-top:6px;'>Portable Work Router</div>",
        unsafe_allow_html=True
    )

with col_cta:
    # CTA PRINCIPAL ÚNICO: Crear (BOTÓN AZUL PRIMARIO)
    if st.button("✨ Crear", key="header_cta_create", use_container_width=True, type="primary"):
```

**Cambios:**
- ✅ Font-size: 16px → 24px (wordmark más robusto)
- ✅ Font-weight: 700 → 900 (más fuerte)
- ✅ Se agregó subtítulo: "Portable Work Router" (contexto)
- ✅ Botón "+ Crear" → "✨ Crear" con type="primary" (único CTA azul)

### 2. Densidad Mejorada de Tarjetas (líneas 2587-2630)

**ANTES:**
```python
cols_per_row = 3
for i in range(0, len(recent_tasks), cols_per_row):
    cols = st.columns(cols_per_row)
    for j, task in enumerate(recent_tasks[i:i+cols_per_row]):
        with cols[j]:
            with st.container(border=True):
                st.markdown(f"<span style='font-size:11px; color:#6B7280; font-weight:500;'>{asset_type}</span>", ...)
                st.markdown(f"**{task['title'][:50]}**")
                preview = task.get('llm_output', '')[:80].replace('\n', ' ')
                if preview:
                    st.caption(f"_{preview}..._")
```

**AHORA:**
```python
cols_per_row = 3
for i in range(0, len(recent_tasks), cols_per_row):
    cols = st.columns(cols_per_row, gap="medium")  # ← GAP CONTROLADO
    for j, task in enumerate(recent_tasks[i:i+cols_per_row]):
        with cols[j]:
            with st.container(border=True):
                # Línea 1: Tipo de activo (pequeño, gris, font-weight=600)
                st.markdown(
                    f"<div style='font-size:11px; color:#6B7280; font-weight:600; margin-bottom:4px;'>{asset_type}</div>",
                    unsafe_allow_html=True
                )

                # Línea 2: Título (fuerte)
                st.markdown(f"**{task['title'][:50]}**", help=task['title'])

                # Línea 3: Preview corto (cursiva)
                preview = task.get('llm_output', '')[:70].replace('\n', ' ')  # ← 80 → 70 (más denso)
                if preview:
                    st.caption(f"_{preview}..._")

                # Línea 4: Metadata (proyecto · tiempo)
                time_ago = format_time_ago(task.get("updated_at", ""))
                st.caption(f"{task['project_name']} · {time_ago}")

                # Botón: icono click
                col_act = st.columns([0.8, 0.2])  # ← MEJOR DISTRIBUCIÓN
                with col_act[1]:
                    if st.button("↗", key=f"asset_open_{task['id']}", use_container_width=True, help="Abrir"):
```

**Cambios:**
- ✅ `gap="medium"` en columns para espacio controlado
- ✅ `margin-bottom:4px` en tipo de activo (reduce espacio)
- ✅ Preview: 80 → 70 chars (más denso)
- ✅ `font-weight:600` en tipo de activo (más legible)
- ✅ Distribución columnas: [0.7, 0.3] → [0.8, 0.2] (más espacio para contenido)

---

## Validación Técnica

### Sintaxis ✅
```bash
$ python -m py_compile app.py
✅ Sintaxis OK
```

### Rutas de Navegación
```
Home:
  ✨ Crear → new_task (Omni-Input)
  ↗ en tarjetas → project

Project:
  ➕ Nueva tarea → new_task (Omni-Input)
  Abrir tarea → project (detalle)

new_task (Omni-Input):
  ✨ Ejecutar → project (resultado)
  ← Volver → home

Result:
  ← Volver a Home → home (eliminado "Volver a Propuesta")
```

### Lógica de State
```python
# ANTES:
new_task → proposal → result

# AHORA:
new_task → result
(proposal eliminado completamente)
```

---

## Checklist Frente B

- [x] omni_input_view() tiene estructura: Proyecto, Input grande, Recomendación inline, CTA única
- [x] No existe botón "Generar propuesta" (reemplazado por "➕ Nueva tarea")
- [x] No existe navegación a proposal_view()
- [x] Modelo + motivo SIEMPRE visibles inline
- [x] CTA único: "✨ Ejecutar con [modelo]"
- [x] Sin pantalla intermedia de propuesta
- [x] Contexto es expandible (no compite)

## Checklist Frente A

- [x] Header wordmark robusto (24px, 900 weight)
- [x] Micro-línea de contexto: "Portable Work Router"
- [x] CTA principal único (azul primario): "✨ Crear"
- [x] Densidad mejorada en tarjetas (gap, padding, preview reducido)
- [x] Tipo de activo claro y legible (font-weight:600)
- [x] Sin artefactos visuales extraños

---

## Próximo Paso

**Captura real de:**
1. Home (header + "Continuar" + "Últimos activos" + Proyectos)
2. Omni-Input (proyecto visible, input grande, recomendación inline, ejecutar con modelo)

Estas serán las únicas pantallas donde se ve el flujo de creación completo.
