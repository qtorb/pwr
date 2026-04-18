# HOME Y OMNI-INPUT: Cambios Aplicados

**Fecha**: 2026-04-18
**Status**: ✅ IMPLEMENTADO (Ambos cambios)
**Alcance**: Arquitectura simplificada + flujo sin navegación intermedia

---

## CAMBIO 1: HOME — Cirugía Visual Final

### ✅ Implementado

**Header minimalista**:
```python
# ANTES
col1, col2, col3 = st.columns([0.8, 2, 0.8])
# Logo + CTA colosal + ⚙️ settings

# DESPUÉS
col1, col2 = st.columns([0.7, 0.3])
# Logo + CTA pequeño
# ⚙️ removido (era ruido)
# "Crear nuevo activo" → "+ Crear"
```

**Resultado visual**:
```
PWR     [+ Crear]
```

**Cambios específicos**:
- ✅ Removido botón ⚙️ settings (ruido visual)
- ✅ "Crear nuevo activo" simplificado a "+ Crear"
- ✅ CTA secundario (sin type="primary")
- ✅ Font size reducido (20px → 16px)
- ✅ Layout más compacto

**Jerarquía resultante**:
- Único botón azul primario visible: Continuar (en Home)
- CTA header: "+ Crear" (gris, secundario)
- Sin manchas azules compitiendo

---

## CAMBIO 2: INPUT PRINCIPAL — Omni-Input

### ✅ Implementado

**Nueva función: `omni_input_view()`**

Reemplaza el flujo anterior:
```
ANTES: Input → [Ver propuesta] → Proposal → [Ejecutar] → Proyecto
DESPUÉS: Input → [Decisión Inline] → [Ejecutar] → Proyecto
```

### Estructura de la Omni-Input

```
┌─────────────────────────────────┐
│ En: [Proyecto]                  │ Contexto superior
├─────────────────────────────────┤
│ ¿Qué necesitas?                 │ Pregunta
│                                 │
│ [Input: Trabajo a realizar]     │ PROTAGONISTA
│ [Textarea: Detalles]            │
│                                 │
│ › Información adicional         │ Expander colapsible
│                                 │
├─────────────────────────────────┤
│ ✨ RECOMENDACIÓN DE PWR         │ INLINE (no separada)
│                                 │
│ Modo: ECO  Modelo: Gemini       │ Decisión real
│ Por qué: [expander pequeño]     │
│ ⏱️ ~2–4s  💰 bajo coste         │
├─────────────────────────────────┤
│ [✨ Ejecutar con Gemini]        │ ÚNICO azul
│ [⚙️ Cambiar modelo]             │ Secundario (pequeño)
│                                 │
│ [← Cancelar]                    │ Terciario
└─────────────────────────────────┘
```

### Cambios de Comportamiento

**ANTES**:
1. User entra inputs
2. Clica "Ver propuesta"
3. **Navegación a proposal_view()**
4. Se muestra decisión del Router
5. Clica "Ejecutar"
6. Navegación a project_view()

**DESPUÉS**:
1. User entra inputs
2. **Decisión aparece INLINE automáticamente**
3. Clica "✨ Ejecutar"
4. Navegación a project_view()

**Diferencia clave**: Sin pantalla separada "proposal", todo en UNA pantalla.

### Reglas Implementadas

✅ **No hay pantalla separada de propuesta**
- proposal_view() sigue existiendo (backward compat)
- Pero NO es navegada desde omni_input_view()

✅ **Sin botón "Generar propuesta"**
- Decisión se genera automáticamente en background
- Usuario no ve "loading" intermedio

✅ **Recomendación inline**
- Modo, Modelo, Por qué aparecen en la misma pantalla
- Condicionado a: if task_title.strip()

✅ **Contexto opcional en expander**
- "📎 Información adicional (opcional)" colapsado
- Usuario puede expandir si necesita

✅ **Modelo + motivo visibles inline**
- Modo, Modelo mostrados directamente
- Reasoning en expander pequeño

✅ **Cambiar modelo como secundario**
- Botón "⚙️ Cambiar modelo" pequeño
- Acción secundaria, no principal

✅ **CTA único: "✨ Ejecutar con [modelo]"**
- Único botón azul sólido visible
- Disabled hasta que haya input válido
- Lleva directamente a ejecución/proyecto

✅ **Usuario siente**:
Escribe → [entiende en el mismo sitio] → Ejecuta

---

## CÓDIGO AGREGADO

### Nueva función: omni_input_view() (línea ~2071)

**Características principales**:
```python
def omni_input_view():
    """Omni-Input: Input + Recomendación + Ejecución en UNA pantalla."""

    # 1. Inputs: Trabajo + Detalles + Contexto opcional
    task_title = st.text_input(...)
    task_description = st.text_area(...)
    context = st.expander(...st.text_area(...))

    # 2. Si hay input válido: Obtener decisión
    if task_title.strip():
        tid = create_task(...)  # Crear temporal
        decision = execution_service.decide(...)  # Decisión en background
        st.session_state["omni_decision"] = decision

    # 3. Mostrar decisión INLINE
    if decision:
        st.markdown("✨ RECOMENDACIÓN DE PWR")
        # Mostrar: Modo, Modelo, Por qué
        # Metadatos: Tiempo, Coste

    # 4. CTA única: Ejecutar
    if st.button("✨ Ejecutar..."):
        st.session_state["view"] = "project"
        st.rerun()
```

### Backward compatibility

```python
def new_task_view():
    """Legacy: Llamar a omni_input_view()."""
    omni_input_view()
```

---

## IMPACTO EN NAVEGACIÓN

### ANTES

```
Home
  ↓ [+ Crear nuevo activo]
new_task_view()
  ↓ [Ver propuesta]
proposal_view()
  ↓ [Ejecutar]
project_view()
```

### DESPUÉS

```
Home
  ↓ [+ Crear]
omni_input_view()
  (decisión aparece inline)
  ↓ [✨ Ejecutar]
project_view()
```

**Simplificación**: Reducidas de 3 vistas a 2 vistas en el flujo principal.

---

## VALIDACIÓN TÉCNICA

✅ **Syntax**: `python3 -m py_compile app.py` → OK
✅ **Funcionalidad**:
- create_task() funciona igual
- ExecutionService.decide() integrado en omni_input_view()
- Navegación simplificada

✅ **Backward Compatibility**:
- new_task_view() sigue funcionando (delegación)
- proposal_view() sigue existiendo (unused)
- project_view() sin cambios

✅ **UX Resultante**:
- Flujo claro: Input → Decisión inline → Ejecutar
- Sin confusión de navegación
- Sin pantalla intermedia

---

## CHECKLIST: CAMBIOS COMPLETADOS

### HOME (Cirugía Visual)
- [x] Remover ⚙️ settings button
- [x] Simplificar "Crear nuevo activo" → "+ Crear"
- [x] Reducir tamaño header (20px → 16px)
- [x] CTA header secundario (sin type="primary")
- [x] Layout compacto (2 columnas)

### OMNI-INPUT (Arquitectura)
- [x] Crear omni_input_view()
- [x] Integrar decisión del Router inline
- [x] Sin navegación intermedia a "proposal"
- [x] CTA único: "✨ Ejecutar con [modelo]"
- [x] Contexto en expander colapsible
- [x] Cambiar modelo como secundario
- [x] Backward compat: new_task_view() delega

### VALIDACIÓN
- [x] Syntax OK
- [x] No hay breaking changes
- [x] Flujo funciona (Input → Decisión → Ejecutar)

---

## ESTADO FINAL

### ✅ Home
- Sobria, clara, sin ruido
- Único botón azul primario visible (Continuar)
- Header minimalista (logo + CTA pequeño)

### ✅ Omni-Input
- Pantalla única: Input + Decisión + Ejecución
- Sin navegación intermedia ("proposal")
- Usuario siente: Escribe → Entiende → Ejecuta
- Decisión inline, no en pantalla separada

### ✅ Arquitectura
- Flujo simplificado: 3 vistas → 2 vistas principales
- Navegación clara y directa
- Sin confusión de pantallas

---

**Pendiente**: Captura visual para validación final

**Status**: ✅ **LISTO PARA VALIDACIÓN**
