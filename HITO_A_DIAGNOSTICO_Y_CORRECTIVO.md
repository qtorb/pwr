# HITO A: DIAGNÓSTICO Y CORRECTIVO ESTRUCTURAL

**Fecha**: 2026-04-18
**Status**: Diagnóstico completado. Plan correctivo propuesto (sin codificar aún).

---

## DIAGNÓSTICO DEL PROBLEMA ACTUAL

### El "Jeroglífico": Qué está mal

**Ubicación del problema**: `project_view()` (lineas ~2290-2700)

**Estructura actual (INCORRECTA):**
```
project_view() → MEZCLA TODO
├── SIDEBAR (25% ancho):
│   ├─ "¿Qué necesitas?"
│   ├─ Input de nueva tarea
│   ├─ Decision previa (automática)
│   ├─ Contexto opcional
│   ├─ Botón "Generar propuesta"
│   ├─ Lista de tareas (ejecutadas vs pendientes)
│   └─ Búsqueda
├── MAIN (75% ancho):
│   ├─ Resumen de tarea
│   ├─ Botón "Ejecutar"
│   ├─ Resultado (si hay)
│   ├─ Caja de guardado
│   ├─ Acciones post-resultado
│   └─ Botones múltiples (Copiar, Crear asset, Mejorar, etc.)
```

**Problemas específicos:**

| Problema | Ubicación | Impacto |
|----------|-----------|--------|
| Input nueva tarea compite con lista de tareas | Sidebar | Usuario no sabe si crear o seleccionar |
| Decision previa se genera automáticamente | Sidebar | No es una pantalla de decisión real, es un adelanto |
| Botón "Generar propuesta" crea tarea | Sidebar | Ambigüedad: ¿es nueva tarea o propuesta? |
| Resultado aparece en MAIN | Main derecha | Si no hay resultado, ¿qué ve? Confusión |
| Demasiados botones azules | Main | Jerarquía destruida (Ejecutar, Copiar, Asset, Mejorar, Compartir, etc.) |
| Header "Cerrar" a la derecha | Top | No es navegación clara, es escape de emergencia |

---

## ANÁLISIS: QUÉ DEBERÍA ESTAR DÓNDE

### Flujo ideal (CORRECTO):

```
Home
  ↓ (click "Nueva Tarea")

PANTALLA 1: NUEVA TAREA (full screen, una intención)
  ├─ Proyecto (contexto superior)
  ├─ Input: Título
  ├─ Input: Descripción
  ├─ Expander: Contexto (opcional)
  └─ CTA: "Ver propuesta" (único botón primario)

  ↓ (click "Ver propuesta")

PANTALLA 2: PROPUESTA (full screen, una intención)
  ├─ Proyecto (contexto superior)
  ├─ Tarea (resumen)
  ├─ Modo: ECO
  ├─ Modelo: Gemini 2.5 Flash Lite
  ├─ Por qué: [motivo breve o desplegable]
  ├─ Tiempo est. / Coste est.
  └─ CTA: "Ejecutar" (único botón primario)

  ↓ (click "Ejecutar")

PANTALLA 3: RESULTADO (full screen, una intención)
  ├─ Proyecto (contexto superior)
  ├─ Tarea (resumen)
  ├─ Resultado (output del Router)
  ├─ Guardado (✅ Guardado en Proyecto)
  ├─ CTA primaria: Una sola
  │   └─ Ej: "Nueva tarea en este proyecto" o "Mejorar análisis"
  └─ CTA secundaria: Máximo 2 (Copiar, Guardar como Asset)
```

---

## PLAN CORRECTIVO: DIVISIÓN DE VISTAS

### Cambio 1: `new_task_view()` → NUEVA PANTALLA PURA

**Qué quedará en NEW_TASK_VIEW:**

```python
def new_task_view():
    """Pantalla de captura: una intención, nada más"""

    # HEADER
    render_header_minimal()

    # CONTENIDO
    st.markdown("## Nueva tarea")
    proyecto = get_project(proyecto_id)
    st.caption(f"En: {proyecto['name']}")

    # INPUTS
    titulo = st.text_input("Título", placeholder="...")
    descripcion = st.text_area("Descripción (opcional)", height=80)

    with st.expander("Contexto (opcional)"):
        contexto = st.text_area("Información relevante...", height=60)

    # CTA PRINCIPAL (ÚNICO)
    if st.button("Ver propuesta", type="primary", use_container_width=True):
        # Crear tarea, ir a PROPOSAL
        st.session_state["view"] = "proposal"
        st.rerun()

    # CTA SECUNDARIA
    if st.button("Cancelar", use_container_width=True):
        st.session_state["view"] = "home"
        st.rerun()
```

**Qué DESAPARECE de NEW_TASK_VIEW:**
- ❌ Decision previa (automática)
- ❌ Lista de tareas
- ❌ Búsqueda
- ❌ Historial de tareas
- ❌ Botón "Cerrar"

---

### Cambio 2: `proposal_view()` → NUEVA PANTALLA PURA (ya existe de Hito A)

**Qué quedará en PROPOSAL_VIEW:**

```python
def proposal_view():
    """Pantalla de decisión: modo, modelo, motivo, nada más"""

    # HEADER
    render_header_minimal()

    # CONTENIDO
    st.markdown(f"## {tarea['title']}")
    st.caption(f"En: {proyecto['name']}")

    # PROPUESTA
    st.markdown("### RECOMENDACIÓN DE PWR")
    col1, col2, col3 = st.columns(3)
    col1.markdown("**Modo**\nECO")
    col2.markdown("**Modelo**\nGemini 2.5 Flash Lite")
    col3.markdown("**Por qué**\nTarea clara, rapidez")

    st.caption("⏱️ ~2-4s  |  💰 Coste bajo")

    # CTA PRINCIPAL (ÚNICO)
    if st.button("Ejecutar", type="primary", use_container_width=True):
        # Ejecutar, ir a RESULT
        st.session_state["view"] = "result"
        st.rerun()

    # CTA SECUNDARIA
    if st.button("Cambiar propuesta", use_container_width=True):
        st.session_state["view"] = "new_task"
        st.rerun()
```

**Qué DESAPARECE de PROPOSAL_VIEW:**
- ❌ Lista de tareas
- ❌ Inputs nuevos
- ❌ Contexto adicional
- ❌ Múltiples alternativas (ECO/RACING visibles al mismo tiempo)

---

### Cambio 3: Nueva `result_view()` → PANTALLA PURA DEL RESULTADO

**Qué estará en RESULT_VIEW:**

```python
def result_view():
    """Pantalla de resultado: output, guardado, 1 acción principal"""

    # HEADER
    render_header_minimal()

    # CONTENIDO
    st.markdown(f"## {tarea['title']}")
    st.caption(f"En: {proyecto['name']}")

    # RESULTADO (output del Router)
    st.markdown("### 📋 Resultado")
    st.markdown(result['output_text'])

    # BLOQUE DE GUARDADO (sobrio)
    st.markdown("---")
    st.markdown("✅ **Guardado**")
    st.caption(f"En proyecto: {proyecto['name']}")
    st.caption(f"Tarea: {tarea['title']}")

    st.markdown("---")

    # METADATA (compacto)
    col1, col2, col3 = st.columns(3)
    col1.metric("Modelo", "Gemini Flash Lite")
    col2.metric("Tiempo", "1.8s")
    col3.metric("Coste", "$0.004")

    # CTA PRIMARIA (UNA SOLA)
    if st.button("Nueva tarea en este proyecto", type="primary", use_container_width=True):
        st.session_state["view"] = "new_task"
        st.rerun()

    # CTA SECUNDARIAS (máximo 2)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Copiar resultado", use_container_width=True):
            st.write("Copiado")
    with col2:
        if st.button("Guardar como Asset", use_container_width=True):
            # Mostrar modal de guardado
            pass
```

**Qué DESAPARECE de RESULT_VIEW:**
- ❌ Inputs nuevos
- ❌ Lista de tareas
- ❌ Botón "Mejorar análisis" (por ahora, Hito E)
- ❌ Múltiples acciones compitiendo

---

### Cambio 4: `project_view()` → MUERE, SE REEMPLAZA POR LAS 3 VISTAS

**Qué pasa con project_view():**
- ❌ ELIMINAR completamente (la funcionalidad se divide en new_task, proposal, result)
- ✅ Si el usuario abre un proyecto, va a Home, no a project_view

**Alternativa futura**: `project_history_view()` (Hito D) que muestre TODAS las tareas del proyecto. Por ahora NO necesaria.

---

## HEADER OBLIGATORIO

### Estructura nueva del header

```
┌──────────────────────────────────────────────────────────┐
│ PWR  >  Proyecto: Marketing 2026  >  Tarea: Resumir...  │
│ [Home]                                                    │
└──────────────────────────────────────────────────────────┘
```

**Componentes:**
1. **Logo**: "PWR" (clickeable → Home)
2. **Jerarquía**: "Proyecto" → "Tarea" → "[Estado]"
3. **Navegación local**: "Home" (botón discreto, no azul chillón)

**Lo que DESAPARECE:**
- ❌ Botón "Cerrar" (reemplazado por Home en breadcrumb)
- ❌ Usuario/Salir (no hay auth aún)
- ❌ Iconos decorativos

---

## JERARQUÍA DE BOTONES: REGLA ESTRICTA

### Regla: 1 primario + 1-2 secundarios máximo

| Pantalla | Primario | Secundario | Terciario |
|----------|----------|-----------|-----------|
| **Nueva Tarea** | "Ver propuesta" | "Cancelar" | — |
| **Propuesta** | "Ejecutar" | "Cambiar" | — |
| **Resultado** | "Nueva tarea" | "Copiar", "Guardar Asset" | — |

**Colores:**
- Primario: `type="primary"` (azul Streamlit)
- Secundario: sin type (gris claro)
- Terciario: discreto o modal

---

## QUÉ SE ELIMINA SIN DISCUSIÓN

| Elemento | Ubicación | Razón |
|----------|-----------|-------|
| project_view() | app.py | Reemplazado por new_task + proposal + result |
| Sidebar en project_view | ~2310 | Eliminado, contenido se distribuye en 3 pantallas |
| Lista de tareas en nueva tarea | Sidebar | Distrae, va a project_history (Hito D) |
| Decision previa (automática) | Sidebar | Reemplazada por proposal_view clara |
| Botón "Cerrar" | Header | Reemplazado por breadcrumb "Home" |
| Múltiples botones azules | Result | Ahora 1 primario + máximo 2 secundarios |

---

## CÓMO VALIDAR QUE EL FLUJO DEJA DE SER CONFUSO

### Criterio de aceptación: El test de los 3 segundos

**Para cada pantalla, preguntar:**

```
1. ¿Dónde estoy?
   → Debe verse en breadcrumb ("PWR > Proyecto > Tarea > [Estado]")

2. ¿Qué paso es?
   → Debe verse el estado actual entre corchetes: [Nueva Tarea], [Propuesta], [Resultado]

3. ¿Qué hago ahora?
   → UN botón debe ser obvio (tipo="primary", más grande, en buena posición)

4. ¿Qué no hay que distraerme?
   → No hay inputs compitiendo, no hay listas de tareas, no hay múltiples botones azules
```

**Test de validación:**

| Test | Nueva Tarea | Propuesta | Resultado |
|------|------------|-----------|-----------|
| ¿Dónde estoy? | Sí (breadcrumb) | Sí (breadcrumb) | Sí (breadcrumb) |
| ¿Qué paso? | [Nueva Tarea] visible | [Propuesta] visible | [Resultado] visible |
| ¿Qué hago? | "Ver propuesta" obvio | "Ejecutar" obvio | "Nueva tarea" obvio |
| ¿Sin distracciones? | Solo input + contexto | Solo propuesta | Solo resultado + guardado |

**Si TODOS pasan → Flujo NO es confuso**

---

## DIAGRAMA DE FLUJO CORRECTIVE

```
HOME (lista de proyectos, no entra en project_view)
  ↓ click "Nueva Tarea"

NEW_TASK_VIEW (pantalla 1)
  Input + Contexto + [Ver propuesta]
  ↓

PROPOSAL_VIEW (pantalla 2)
  Modo | Modelo | Por qué + [Ejecutar]
  ↓

RESULT_VIEW (pantalla 3)
  Output + Guardado + [Nueva tarea en este proyecto]
  ↓

Back to HOME or NEW_TASK
```

**Cada pantalla REEMPLAZA la anterior. No coexisten.**

---

## RESUMEN PARA IMPLEMENTACIÓN

| Acción | Pantalla | Archivo | Cambio |
|--------|----------|---------|--------|
| Refactorizar | new_task_view | app.py | Simplificar a inputs + "Ver propuesta" |
| Mantener | proposal_view | app.py | Ya existe de Hito A, confirmar estructura |
| Crear | result_view | app.py | Nueva función (~100 líneas) |
| Eliminar | project_view | app.py | Removida completamente (~400 líneas) |
| Actualizar | routing en main() | app.py | 5 vistas → new_task, proposal, result, radar, home |

---

**Status**: Plan correctivo listo. Esperando aprobación de Albert antes de codificar.

*¿Aprobá este plan correctivo, o hay ajustes que hacer?*
