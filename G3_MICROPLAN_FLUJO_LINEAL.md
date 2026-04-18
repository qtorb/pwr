# G3: FIRST-TASK FLOW EXPLÍCITO — MICROPLAN

## DECISIÓN APROBADA

Implementar flujo principal lineal con un CTA primario por estado, sidebar contexto-only, menos acciones compitiendo.

---

## 1. ARCHIVOS A TOCAR

### app.py (único archivo)

| Sección | Acción | Líneas aprox |
|---------|--------|--------------|
| **onboarding_view()** | Reorganizar pasos en secuencia 1-4 | 1868-2000 |
| **new_task_view()** | Secuencia idéntica a A, sin historial | 2078-2162 |
| **home_view()** | Reorganizar Home como "Retomar O Crear" | 2163-2269 |
| **main() - sidebar** | Cambiar a contexto-only | 3081-3111 |
| **main() - project_selector()** | Evaluar si mantener o simplificar | 3111 |
| Nada más | No tocar router, BD, ExecutionService | — |

---

## 2. QUÉ DESAPARECE DE CADA ESTADO

### ESTADO A (Onboarding)

#### Desaparece completamente:
- ❌ **Tabs Home/Radar** en el onboarding
  - Radar se accesa vía link discreta al final
  - Input es la acción 1 (no compite con tabs)

- ❌ **Ejemplos como botones prominentes** ([Resume] [Escribe] [Analiza])
  - Convertir a captions/sugestiones discretas debajo del input
  - O como dropdown/pills (no botones)
  - Propósito: Inspiración, no acción principal

- ❌ **Micro-guía** ("Tu tarea entra → PWR elige → Obtienes resultado")
  - Innecesario si flujo es lineal
  - Los pasos hablan por sí solos

- ❌ **Decision preview como bloque separado**
  - Se muestra automáticamente debajo del input
  - No pide acción, solo informa

#### Queda muy secundario:
- ⬇️ **"Otra tarea rápida"** (después de resultado)
  - Solo aparece en PASO 4 (resultado)
  - No compite con "Empezar"

- ⬇️ **Radar link** (al final, tamaño muy pequeño)
  - Texto: "Explorar modelos →" (opcional)
  - Ubicación: Última línea de resultado

---

### ESTADO B (Nueva tarea)

#### Desaparece:
- ❌ **Nada principal**
  - Ya está limpio post-G2

#### Queda muy secundario:
- ⬇️ **Botón "← Volver"**
  - Reducir tamaño, ponerlo en esquina
  - No es acción, es salida

- ⬇️ **Radar**
  - No aparece (ir a Home si quieres explorar)

---

### ESTADO C (Home)

#### Desaparece completamente:
- ❌ **Input "¿Qué necesitas hacer ahora?" arriba**
  - Eso es ESTADO B
  - Home es SOLO navegación

- ❌ **Tabs (si existen)**
  - No hay tabs en Home con actividad
  - Tabs SOLO en onboarding

- ❌ **Grid "Mis proyectos" como sección principal**
  - Mover abajo o dentro de expandible
  - "Trabajo en progreso" es lo primero

- ❌ **Botón "Crear primer proyecto"**
  - Duplicado con "Crear proyecto"

- ❌ **Sidebar con lista de proyectos**
  - Va a contexto-only (solo si abierto)
  - Home es la fuente de verdad

#### Queda muy secundario:
- ⬇️ **"Crear proyecto"**
  - Dentro de expandible o sección "Avanzado"
  - O botón pequeño al final

- ⬇️ **Radar**
  - Link pequeño (si acaso)

---

## 3. QUÉ SE MUEVE A CADA VISTA

### De A a B (funcionalidad, no código):

| Elemento | Ahora en A | Mover a B | Motivo |
|----------|-----------|-----------|--------|
| Input para nueva tarea | A (onboarding) | No (es onboarding) | A es para usuario nuevo |
| Input para tarea en proyecto | No existe | B (new_task_view) | Crear tarea dentro proyecto |
| Decision preview | A | B | Ambas lo usan |
| Botón ejecutar | A: "Empezar" | B: "Generar" | Mismo propósito, diferente contexto |
| Contexto opcional | No existe | B | Refinamiento de tarea |

**Conclusión:** No hay "movimiento" entre A-B. Ambas son flujos paralelos independientes.

### De C a new_task_view:

| Elemento | Ahora en C | Mover a B | Motivo |
|----------|-----------|-----------|--------|
| Input + decision + contexto + CTA | En C (home) | Todo a B | Input NO debe estar en Home |

**Cambio:** Home pierde input. Input va SOLO a new_task_view (B).

---

## 4. CÓMO QUEDA SIDEBAR CONTEXTO-ONLY

### Implementación en Streamlit:

```python
# En main(), sidebar
with st.sidebar:
    st.markdown("### PWR")
    st.divider()

    # NAVEGACIÓN PRINCIPAL (siempre)
    st.markdown("#### Navegación")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏠 Home", use_container_width=True,
                     type="primary" if current_view == "home" else "secondary",
                     key="nav_home"):
            st.session_state["view"] = "home"
            st.session_state["active_project_id"] = None
            st.rerun()
    with col2:
        if st.button("📡 Radar", use_container_width=True,
                     type="primary" if current_view == "radar" else "secondary",
                     key="nav_radar"):
            st.session_state["view"] = "radar"
            st.rerun()

    st.divider()

    # CONTEXTO (solo si aplica)
    st.markdown("#### Contexto")

    # IF proyecto abierto
    active_project_id = st.session_state.get("active_project_id")
    if active_project_id:
        with get_conn() as conn:
            project = conn.execute(
                "SELECT name FROM projects WHERE id = ?",
                (active_project_id,)
            ).fetchone()
            if project:
                st.caption(f"📁 **{project['name']}**")
                if st.button("Abrir proyecto", use_container_width=True,
                            key="sidebar_open_project"):
                    st.session_state["view"] = "project"
                    st.rerun()

    # IF tarea seleccionada
    selected_task_id = st.session_state.get("selected_task_id")
    if selected_task_id:
        task = get_task(selected_task_id)
        if task:
            st.caption(f"📌 {task['title'][:30]}")

    # Si nada, mostrar hint
    if not active_project_id and not selected_task_id:
        st.caption("*Selecciona un proyecto para ver contexto*")
```

### Resultado visual:

```
┌─────────────────────┐
│     PWR             │
├─────────────────────┤
│ Navegación          │
│ [🏠 Home] [📡 Radar]│
├─────────────────────┤
│ Contexto            │
│ 📁 Mi primer proyc. │
│ [Abrir proyecto]    │
│                     │
│ (o: "Selecciona..." │
│  si no hay contexto)│
└─────────────────────┘
```

**Ventajas:**
- ✅ Sidebar es "espejo del estado"
- ✅ Nunca duplica Home
- ✅ No compite con contenido
- ✅ Minimalista (no distrae)

---

## 5. PATRÓN CONDICIONAL STREAMLIT

### ESTADO A: Flujo lineal secuencial

```python
def onboarding_view():
    """
    ESTADO A: Flujo 1-2-3-4 aparecen secuencialmente
    """
    st.markdown("### 1. ¿Cuál es tu tarea?")
    st.caption("Describe lo que necesitas hacer")

    input_text = st.text_area(
        "",
        placeholder="Ej: Resume este documento...",
        height=90,
        key="onboard_input",
        label_visibility="collapsed"
    )

    # PASO 2: Aparece si hay input
    if input_text.strip():
        st.write("")
        st.markdown("### 2. Cómo lo vamos a resolver")

        task_input = TaskInput(...)
        decision = execution_service.decision_engine.decide(task_input)

        # Mostrar propuesta (no pide acción)
        if decision.mode == "eco":
            st.info("**Tarea clara y directa** → Vamos a usar un modo rápido")
        else:
            st.info("**Tarea que necesita análisis** → Vamos a usar un modo potente")

        st.write("")
        st.markdown("### 3. Ejecuta")

        # PASO 3: CTA principal
        if st.button("✨ Empezar", use_container_width=True,
                     type="primary", key="onboard_execute"):
            # Ejecutar
            result = execute(...)

            # PASO 4: Resultado
            st.write("")
            st.markdown("### 4. Resultado")
            st.markdown(result.output_text)

            st.write("")
            st.caption("✓ Tarea guardada en tu proyecto")

            # Opcionales después de resultado
            st.write("")
            col1, col2, col3 = st.columns(3, gap="small")
            with col1:
                if st.button("🚀 Otra tarea", use_container_width=True):
                    st.session_state["onboard_input"] = ""
                    st.rerun()
            # ... etc
```

**Patrón:** `if input → show paso 2 → if button → show paso 3-4`

---

### ESTADO B: Idéntico al A (flujo lineal)

```python
def new_task_view():
    """
    ESTADO B: Flujo 1-2-3-4 idéntico a A
    """
    # Botón volver en esquina (muy pequeño)
    col1, col2 = st.columns([0.95, 0.05])
    with col2:
        if st.button("←", key="back"):
            st.session_state["view"] = "home"
            st.rerun()

    st.markdown("### 1. ¿Qué necesitas?")
    input_text = st.text_area(...)

    if input_text.strip():
        st.markdown("### 2. Cómo lo vamos a resolver")
        decision = show_preview(input_text)

        st.markdown("### 3. Detalles (opcional)")
        with st.expander("Contexto"):
            context = st.text_area(...)

        st.markdown("### 4. Ejecuta")
        if st.button("✨ Generar", use_container_width=True, type="primary"):
            # Ejecutar
            result = execute(...)
            # Mostrar resultado...
```

---

### ESTADO C: Dos caminos claros

```python
def home_view():
    """
    ESTADO C: No hay input arriba. Solo navegación.
    """
    if not has_activity:
        onboarding_view()
        return

    # Home con actividad
    st.markdown("### ¿Qué quieres hacer?")

    st.write("")

    # OPCIÓN 1: Retomar
    st.markdown("#### Retomar trabajo")
    recent_tasks = get_recent_executed_tasks(limit=5)
    if not recent_tasks:
        st.caption("No hay tareas recientes")
    else:
        cols_per_row = 3
        for i in range(0, len(recent_tasks), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, task in enumerate(recent_tasks[i:i+cols_per_row]):
                with cols[j]:
                    st.markdown(f"**{task['title'][:30]}**")
                    if st.button("Continuar", key=f"continue_{task['id']}",
                                use_container_width=True):
                        st.session_state["active_project_id"] = task["project_id"]
                        st.session_state["selected_task_id"] = task["id"]
                        st.rerun()

    st.write("")
    st.divider()
    st.write("")

    # OPCIÓN 2: Crear algo nuevo
    st.markdown("#### O crear algo nuevo")
    if st.button("➕ Nueva tarea", use_container_width=True,
                type="primary", key="new_task_btn"):
        st.session_state["view"] = "new_task"
        st.rerun()

    st.write("")

    # Secundario: Proyectos (expandible O grid pequeño)
    with st.expander("Mis proyectos", expanded=False):
        projects = get_projects_with_activity()
        if not projects:
            st.caption("No hay proyectos")
        else:
            cols_per_row = 2
            for i in range(0, len(projects), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, project in enumerate(projects[i:i+cols_per_row]):
                    with cols[j]:
                        st.markdown(f"**{project['name'][:25]}**")
                        if st.button("Abrir", key=f"open_{project['id']}",
                                    use_container_width=True):
                            st.session_state["active_project_id"] = project["id"]
                            st.rerun()

    st.write("")

    # Terciario: Crear proyecto (muy discreto)
    with st.expander("Crear nuevo proyecto"):
        # Form aquí
        ...
```

**Patrón:** Dos opciones sin competencia (Retomar vs Crear). Secundarios expandibles.

---

## 6. QUÉ NO TOCARÁS

### Off-limits (NUNCA modificar):

| Componente | Razón |
|------------|-------|
| **router.py** | Lógica de decisión intacta |
| **BD schema** | Estructura igual |
| **ExecutionService** | Ejecución sin cambios |
| **project_view()** | Funciona bien, no toca |
| **create_task(), save_*()** | Helpers sin cambios |
| **CSS/inyecciones** | Mantener igual |
| **project_selector()** | Evaluable, pero secundario |

---

## 7. VALIDACIÓN: ¿PRÓXIMO PASO OBVIO?

### Test A: Observación sin instrucciones

**ESTADO A (Onboarding):**
```
Observer entra sin hablar:
  ¿Mira el input primero?
  ¿Entiende que "Empezar" ejecuta?
  ¿Sabe qué hacer después?

ÉXITO:
  "1. Escribo aquí → 2. Dice cómo lo resuelve →
   3. Clico Empezar → 4. Veo resultado"

FALLO:
  "¿Qué son todos estos elementos?"
```

**ESTADO B (Nueva tarea):**
```
Observer entra sin hablar:
  ¿Ve input como acción 1?
  ¿Entiende "Generar"?
  ¿Sabe si contexto es obligatorio?

ÉXITO:
  "Escribo, veo propuesta, genero"

FALLO:
  "¿Diferencia con la otra pantalla?"
```

**ESTADO C (Home):**
```
Observer entra sin hablar:
  ¿Ve "Retomar" vs "Crear"?
  ¿Ignora sidebar naturalmente?
  ¿Siguiente acción es obvia?

ÉXITO:
  "Veo mis tareas. Clico una para retomar O clico
   'Nueva tarea' para hacer algo nuevo"

FALLO:
  "¿Dónde está el input? ¿Qué es el sidebar?"
```

### Test B: Pregunta directa (después de flujo)

**Para cada estado:**
> "Sin releer, ¿cuál fue el próximo paso en cada momento?"

| Paso | Respuesta esperada |
|------|-------------------|
| A.1 | "Escribir en el input" |
| A.2 | "Ver la propuesta" (automático) |
| A.3 | "Clickear Empezar" |
| A.4 | "Ver resultado" |
| — | — |
| B.1 | "Escribir en el input" |
| B.2 | "Ver la propuesta" |
| B.3 | "Opcionalmente contexto" |
| B.4 | "Clickear Generar" |
| — | — |
| C.1 | "Retomar una tarea O crear nueva" |
| C.2 | "(De retomar) Entrar a tarea" |
| C.2 | "(De crear) Ir a new_task_view" |

### Test C: Métrica cuantitativa

**Tiempo a acción primaria (sin leer copy):**
- Goal: < 5 segundos usuario entienda qué hacer
- Medida: Toma un usuario nuevo, mide cuándo clickea el primer botón/input

**Métrica: "¿El siguiente paso es obvio?"**
- Si 80%+ usuarios dicen "sí" sin ayuda → **G3 ganó**
- Si < 80% → Refinar

---

## 8. CAMBIOS ESPECÍFICOS POR LÍNEAS

### ESTADO A (onboarding_view):

| Líneas | Cambio | Detalle |
|--------|--------|---------|
| 1880-1900 | Reorganizar | Pasos 1-2-3-4 numerados |
| 1905-1927 | Ejemplos → sugestiones | No botones, caps discretas |
| 1930-1956 | Decision preview integrado | Automático si input, no tab |
| 1960-2064 | Botón "Empezar" → paso 3 | ÚNICO CTA principal |
| 2068-2074 | Resultado → paso 4 | Secuencial |
| 2078-2000 | Tabs desaparecen | Radar link abajo |

### ESTADO B (new_task_view):

| Líneas | Cambio | Detalle |
|--------|--------|---------|
| 2081-2086 | Botón volver → esquina | Pequeño, no prominente |
| 2088-2162 | Pasos 1-2-3-4 | Idéntico a A |

### ESTADO C (home_view):

| Líneas | Cambio | Detalle |
|--------|--------|---------|
| 2163-2180 | Quitar input arriba | Input SOLO en B |
| 2182-2220 | "Trabajo en progreso" → primero | Opción 1 |
| 2225-2241 | "Nueva tarea" como CTA primario | Opción 2, prominente |
| 2245-2269 | Proyectos → expandible O abajo | Secundario |

### Sidebar (main):

| Líneas | Cambio | Detalle |
|--------|--------|---------|
| 3081-3111 | Reescribir sidebar | Contexto-only (si proyecto/tarea) |

---

## STATUS TECH REAL

| Aspecto | Estado | Detalles |
|---------|--------|----------|
| **Microplan** | ✅ Completado | 8 secciones detalladas |
| **Archivo** | ✅ app.py único | 4 secciones a reorganizar |
| **Desapariciones** | ✅ Mapeadas | Tabs, ejemplos buttons, input en C |
| **Flujo lineal** | ✅ Definido | Pasos 1-2-3-4 secuenciales |
| **Sidebar** | ✅ Especificado | Contexto-only, código Streamlit incluido |
| **Patrón** | ✅ Detallado | If/then para pasos secuenciales |
| **Validación** | ✅ Método | Observación + pregunta directa + métrica |
| **Riesgos** | ⚠️ Bajo | Refactor UI puro, no toca backend |
| **Próximo** | ⏳ Implementación | Cuando apruebes este microplan |

---

## DECISIÓN QUE NECESITO

**¿Apruebo este microplan G3?**

1. **✅ Sí, exacto así** → Empiezo implementación (ETA ~90 min)
2. **⚠️ Ajustes antes** → Dime qué cambiar
3. **❌ Volvemos atrás** → Reconsideramos G3

**Mi recomendación:** El microplan es muy concreto, bajo riesgo. **Sí, proceder.**

---

**FIN DE MICROPLAN G3**
