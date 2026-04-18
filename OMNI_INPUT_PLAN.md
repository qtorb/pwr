# OMNI-INPUT: Plan de Redesign Real

**Problema Actual**:
```
Input → [Ver propuesta] → Proposal Screen → [Ejecutar] → Execution
```
Dos pantallas, dos navegaciones, confusión.

**Solución: Omni-Input**:
```
Single Screen: Input → [Decisión inline] → [Ejecutar con Modelo]
```

---

## ESTRUCTURA DE LA OMNI-INPUT

### Layout
```
┌─────────────────────────────────────┐
│ En: [Proyecto]                      │ ← Contexto superior
├─────────────────────────────────────┤
│ ¿Qué necesitas hacer?               │ ← Pregunta única
│                                     │
│ [Input grande: textarea]            │ ← Protagonista
│                                     │
│ › Contexto (opcional)               │ ← Expander colapsado
│                                     │
├─────────────────────────────────────┤
│ ✨ RECOMENDACIÓN DE PWR             │ ← Inline, no separada
│                                     │
│ Modo: ECO  Modelo: Gemini           │ ← Datos reales
│ Por qué: [pequeño expander]         │
│                                     │
│ ⏱️ ~2–4s  💰 Bajo coste             │
├─────────────────────────────────────┤
│ [✨ Ejecutar con Gemini]            │ ← ÚNICO botón azul
│ [⚙️ Cambiar modelo (pequeño)]       │ ← Secundario
│                                     │
│ [← Cancelar]                        │ ← Tertiary
└─────────────────────────────────────┘
```

---

## CAMBIOS A NIVEL DE CÓDIGO

### 1. new_task_view() → Omni-Input
**Antes**:
```python
# new_task_view: Input + "Ver propuesta"
# proposal_view: Decisión mostrada
# project_view: Ejecución
```

**Después**:
```python
# omni_input_view: Input + Decisión + Ejecución
# Todo en UN view
```

### 2. Flujo lógico

**Paso 1**: Usuario ingresa input
- Título + Descripción (obligatorio/opcional)
- Contexto en expander (opcional)

**Paso 2**: Mostrar recomendación (INLINE)
```python
if task_title.strip():
    # Crear tarea temporal
    tid = create_task(...)

    # Obtener decisión del Router (sin screen separada)
    decision = execution_service.decide(task_input)

    # Mostrar decisión INLINE
    render_proposal_inline(decision)

    # CTA único: Ejecutar
    if st.button("✨ Ejecutar con [modelo]"):
        execute_task(tid)
```

**Paso 3**: Ejecutar directamente
- NO hay "Ver propuesta" como navegación
- NO hay proposal_view() separada
- Ejecución acontece en el mismo view o en project_view() simplemente

---

## DECISIONES ARQUITECTÓNICAS

### NO tocar:
- project_view() (la ejecución real sigue igual)
- proposal_view() (podría quedar como respaldo)
- base de datos (execution_status sigue igual)

### SÍ cambiar:
- new_task_view() → Omni-Input
- Flujo de navegación: "new_task" → proyecto/ejecución (sin "proposal")
- Eliminar "Ver propuesta" como CTA separador

### Resultado:
```
Home → [+ Crear] → Omni-Input → [Ejecutar] → Ejecución/Proyecto
```

---

## REGLAS PARA LA OMNI-INPUT

1. ✅ Sin pantalla separada de propuesta
2. ✅ Sin botón "Generar propuesta"
3. ✅ Recomendación inline (aparece solo si hay input válido)
4. ✅ Contexto en expander collapsible
5. ✅ Modelo + motivo visibles inline
6. ✅ Cambiar modelo como acción SECUNDARIA
7. ✅ CTA único visible: "✨ Ejecutar con [modelo]"
8. ✅ Usuario siente: escribe → entiende cómo se resuelve → ejecuta

---

## CAMBIOS ESPECÍFICOS

### Cambio 1: Rename y refactor new_task_view()
```python
def omni_input_view():
    """
    Pantalla única de entrada + recomendación + ejecución.
    """
    # Inputs...
    # Si hay input válido → Mostrar decisión inline
    # CTA: Ejecutar directamente
```

### Cambio 2: Naveg ación (main())
```python
# ANTES
if st.session_state["view"] == "new_task":
    new_task_view()
elif st.session_state["view"] == "proposal":
    proposal_view()
elif st.session_state["view"] == "project":
    project_view()

# DESPUÉS
if st.session_state["view"] == "new_task":
    omni_input_view()  # Todo en uno
elif st.session_state["view"] == "project":
    project_view()
# proposal_view() ya no es llamada desde la navegación principal
```

### Cambio 3: Eliminar navegación a "proposal"
```python
# ANTES
st.session_state["view"] = "proposal"

# DESPUÉS
# No existe. El flujo es: input → decision inline → ejecutar
# Al ejecutar, pasa directamente a project_view()
```

---

## IMPLEMENTACIÓN POR PASOS

### Paso 1: Crear omni_input_view() (nueva función)
- Copia de new_task_view()
- Integra lógica de proposal_view() (decision engine)
- Muestra recomendación inline
- CTA único: Ejecutar

### Paso 2: Actualizar main() (routing)
- Cambiar "new_task" → omni_input_view()
- Eliminar llamada a proposal_view()
- Mantener project_view() igual

### Paso 3: Actualizar navegación
- Botones que iban a "proposal" ahora van a ejecución/proyecto
- Eliminar intermediario

### Paso 4: Pruebas
- Flujo completo: Crear → Input → Decisión inline → Ejecutar
- Verificar que NO hay navegación a proposal_view()
- Verificar que modelo selector funciona

---

## ESTADO FINAL DESEADO

✅ **Comportamiento**:
- Usuario abre Home, clica "+ Crear"
- Ve pantalla con input grande
- Escribe algo
- Ve recomendación inline (sin navegación a otra pantalla)
- Clica "✨ Ejecutar"
- Pasa a ejecución/proyecto

❌ **Lo que DESAPARECE**:
- "Ver propuesta" como botón/navegación
- proposal_view() como pantalla visible
- Dos pantallas separadas

---

**Ready for Implementation**
