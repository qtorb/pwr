# G4: MICROPLAN — Composición Visual del Onboarding

## OBJETIVO
Reorganizar `onboarding_view()` para que **la secuencia se sienta, no se explique**.

INPUT = protagonista. Todo lo demás = apoyo.

---

## 1. ARCHIVOS A TOCAR

**ÚNICO:** `app.py`
- Función: `onboarding_view()` (líneas 1868-2043)
- **Nada más.** No tocar: router.py, BD, ExecutionService, helpers, styles, otros views

**Estimado de cambio:** ~40 líneas (eliminar + reorganizar)

---

## 2. ESTRUCTURA VISUAL NUEVA

### Antes (G3 — FALLA en jerarquía):
```
[🚀 Portable Work Router] ← ELIMINAR
[Explicación 3 puntos] ← ELIMINAR
[Espaciado]
### 1. ¿Cuál es tu tarea? ← ELIMINAR
[Input 90px]
[💡 Ejemplos...] ← invisible
[Espaciado]
### 2. Cómo... [condicional] ← ELIMINAR header
[Decision preview]
[Espaciado]
### 3. Ejecuta [condicional] ← ELIMINAR
[✨ Empezar]
[Espaciado]
### 4. Resultado [condicional] ← ELIMINAR
[Display]
```

### Después (G4 — INPUT protagonista):
```
¿Cuál es tu tarea?
[Input 120px - PROTAGONISTA, height=120]
Ejemplo rápido: Resume, Escribe, Analiza

[ESPACIO PEQUEÑO]

[SI input.strip()] ↓
[Decision preview - AUTOMÁTICO, sin header]
[ESPACIO PEQUEÑO]
[✨ Empezar] - PRIMARY, AUTOMÁTICO

[ESPACIO PEQUEÑO]

[SI ejecutado] ↓
[Resultado - AUTOMÁTICO, sin header]
```

**Cambios clave:**
1. INPUT es primer elemento (después de 1 línea)
2. INPUT es más grande (120px vs 90px)
3. Ejemplos visibles en copy (no caption)
4. Headers "#" eliminados (3 menos)
5. Espacios colapsados (máximo 1)
6. Propuesta + Botón + Resultado = automáticos, sin "headers de paso"

---

## 3. QUÉ DESAPARECE

| Elemento | Línea aprox | Razón | Impacto |
|----------|-------------|-------|--------|
| `st.title("🚀 PWR")` | 1879 | Redundante (en sidebar) | Gana espacio, claridad |
| Explicación 3 puntos | 1882-1887 | Abstracta, requiere lectura | Quita ruido |
| `st.write("")` multiple | 1889, 1906, 1926, 2032 | Crea pasos visuales falsos | Densidad |
| `st.markdown("### 1.")` | 1892 | Confunde (no ayuda) | Simplicidad |
| `st.caption("💡 Ejemplos")` | 1904 | Invisible | Se reemplaza con copy |
| `st.markdown("### 2.")` | 1910 | Innecesario | Claridad |
| `st.markdown("### 3.")` | 1929 | Innecesario | Claridad |
| `st.markdown("### 4.")` | 2036 | Innecesario | Claridad |

**Total líneas a eliminar:** ~15
**Total líneas a reorganizar:** ~25

---

## 4. QUÉ QUEDA + QUÉ CAMBIA

### QUEDA INTACTO:
```python
# Inicializar ExecutionService
execution_service = ExecutionService(conn)

# Toda la lógica de captura (TaskInput, decide, create_task)
# Toda la lógica de ejecución (execute, save_execution_result)
# Toda la lógica de sesión (session_state updates)
# display_decision_preview(decision, capture_title)
# display_onboarding_result(result, task, is_first_execution=True)
```

**Nada de lógica cambia. Solo UI.**

### CAMBIA:

#### A. Input — de 90px a 120px
```python
# ANTES
capture_title = st.text_area(
    "",
    placeholder="Ej: resume un documento • escribe un email • analiza un gráfico • propón un plan",
    key="onboard_capture_input",
    height=90,  # ← pequeño
    label_visibility="collapsed"
)

# DESPUÉS
capture_title = st.text_area(
    "¿Cuál es tu tarea?",  # ← Label EN el input
    placeholder="Resume un documento • Escribe un email • Analiza un gráfico • Propón un plan",
    key="onboard_capture_input",
    height=120,  # ← más grande
    label_visibility="visible"  # ← visible
)
```

**Por qué:**
- Input es PROTAGONISTA → label visible, size mayor
- Label integrado (no header separado)
- Ejemplos van en placeholder (más claro)

#### B. Ejemplos — de caption a ayuda visible
```python
# ANTES
if not capture_title.strip():
    st.caption("💡 Ejemplos: Resume, Escribe, Analiza")

# DESPUÉS
st.caption("Ejemplo: Resume un documento • Escribe un email • Analiza un gráfico")
# SIEMPRE visible, no condicional
```

**Por qué:**
- Usuario ve ejemplos antes de escribir
- Discreta pero visible (caption está bien)
- Guía sin ser intrusiva

#### C. Decision preview — sin header
```python
# ANTES
st.markdown("### 2. Cómo lo vamos a resolver")
display_decision_preview(decision, capture_title)

# DESPUÉS
display_decision_preview(decision, capture_title)
# Sin header, solo el contenido
```

#### D. Botón — sin header, visible automático
```python
# ANTES
st.markdown("### 3. Ejecuta")
if st.button("✨ Empezar", use_container_width=True,
             key="onboard_capture_btn", type="primary"):

# DESPUÉS
if st.button("✨ Empezar", use_container_width=True,
             key="onboard_capture_btn", type="primary"):
# Sin header, botón es claro por sí
```

#### E. Resultado — sin header
```python
# ANTES
st.markdown("### 4. Resultado")
display_onboarding_result(result, task, is_first_execution=True)

# DESPUÉS
display_onboarding_result(result, task, is_first_execution=True)
# Sin header, resultado es claro por sí
```

#### F. Espacios — colapsados
```python
# ANTES: st.write("") aparece 5+ veces

# DESPUÉS: máximo 1 espacio entre secciones principales
st.write("") # Después de ejemplos
# [decision preview]
# [botón]
st.write("") # Después de botón
# [resultado]
```

---

## 5. COMPOSICIÓN VISUAL FINAL (Paso a paso)

### **PASO 1: INPUT INMEDIATO**
```
[¿Cuál es tu tarea?]
[Input 120px - PROTAGONISTA]
```
Propósito: Usuario sabe qué hacer en 1 segundo.

### **PASO 2: EJEMPLO DISCRETO**
```
Ejemplo: Resume un documento • Escribe un email • Analiza un gráfico
[caption pequeño]
```
Propósito: Si no sabe qué escribir, hay referencias.

### **PASO 3: PROPUESTA AUTOMÁTICA** (si input.strip())
```
[Decision preview - aparece automático, sin header]
[Cómo PWR lo resolvería]
```
Propósito: Feedback inmediato de lo que pasaría.

### **PASO 4: BOTÓN CLARO** (si input.strip())
```
[✨ Empezar] - PRIMARY button, full width
```
Propósito: Siguiente paso obvio.

### **PASO 5: RESULTADO AUTOMÁTICO** (si ejecutado)
```
[Resultado del modelo - aparece automático]
[CTAs: Copiar / Otra tarea / Ver proyecto]
```
Propósito: Mostrar éxito, opciones siguientes.

---

## 6. PATRÓN CONDICIONAL STREAMLIT

```python
# PASO 1: SIEMPRE visible
st.text_area(...)
st.caption("Ejemplo...")

# PASO 2: Si input tiene contenido
if capture_title.strip():
    display_decision_preview(...)

    # PASO 3: Botón también condicional
    if st.button("✨ Empezar", ...):
        # Ejecutar lógica
        # ...
        st.session_state["onboard_result_ready"] = True
        st.rerun()

# PASO 4: Si completado
if st.session_state.get("onboard_result_ready"):
    display_onboarding_result(...)
```

**Patrón:** Vertical, automático, sin "headers de paso".

---

## 7. QUÉ NO TOCAS

```
✅ ExecutionService initialization
✅ TaskInput creation
✅ decision_engine.decide()
✅ create_project() / create_task()
✅ execution_service.execute()
✅ save_execution_result()
✅ display_decision_preview() function
✅ display_onboarding_result() function
✅ Session state logic
✅ Routing en main()
✅ new_task_view()
✅ home_view()
✅ project_view()
```

**NADA de lógica de negocio. UI pura.**

---

## 8. CÓMO VALIDARÁS QUE FUNCIONA

### Test 1: "Sin leer, ¿qué hago?"
```
Usuario nuevo entra al onboarding.
Observación: ¿Dónde mira primero? ¿Qué ve?

✅ ÉXITO: "Hay un input grande, escribo ahí"
❌ FALLO: "Leo un título, luego texto, luego busco dónde escribir"
```

### Test 2: "Flujo automático"
```
Usuario escribe en input.
Observación: ¿Qué aparece debajo?

✅ ÉXITO: "Automáticamente veo qué pasaría + botón"
❌ FALLO: "Nada pasa, o veo headers confundidores"
```

### Test 3: "Progresión natural"
```
Usuario clica botón.
Observación: ¿Se siente como un paso natural?

✅ ÉXITO: "Clicar botón → resultado automático"
❌ FALLO: "Saltos, loading largo, confusión de transición"
```

### Test 4: "Métrica: vistazo de 2 segundos"
```
Pregunta a usuario nuevo: "Sin instrucciones, ¿qué es esto?"

✅ ÉXITO (80%+): "Un lugar donde descripir tareas y PWR las hace"
❌ FALLO: "Un sistema de pasos", "una explicación", vaguedad
```

---

## 9. RIESGOS Y MITIGACIONES

| Riesgo | Probabilidad | Mitigación |
|--------|-------------|-----------|
| Eliminar elemento crítico | ⚠️ Baja | Todas las líneas a eliminar son UI. Lógica intacta. |
| Cambiar height input quebró layout | 🔴 Muy baja | Input es responsivo en Streamlit. 90→120 es seguro. |
| display_decision_preview() falla sin header | 🔴 Muy baja | Function es agnóstica de contexto. |
| Session state corruption | 🔴 Muy baja | Lógica de sesión NO CAMBIA. |
| Routing rompe | 🔴 Muy baja | main() NO CAMBIA. |

**Riesgo general:** ⚠️ **MUY BAJO** (UI pura, sin lógica)

---

## 10. CHECKLIST DE IMPLEMENTACIÓN

```
Antes de codificar:
[ ] Leer diagnostico G4 completo
[ ] Entender que es UI pura, sin riesgos de lógica

Durante codificación:
[ ] Eliminar st.title()
[ ] Eliminar explicación 3 puntos
[ ] Cambiar input: height 120, label_visibility visible
[ ] Cambiar ejemplos: siempre visible, mejorado copy
[ ] Eliminar headers "### 1", "### 2", etc
[ ] Eliminar st.write("") múltiples
[ ] Mantener lógica de ejecución INTACTA
[ ] Verificar sintaxis (python -m py_compile)

Después codificación:
[ ] Validar Test 1: "Sin leer, ¿qué hago?"
[ ] Validar Test 2: "Flujo automático"
[ ] Validar Test 3: "Progresión natural"
[ ] Validar Test 4: "Vistazo 2 segundos"
[ ] Si 80%+ usuarios entienden → G4 ÉXITO
```

---

## 11. STATUS TÉCNICO REAL

| Aspecto | Estado | Detalle |
|---------|--------|--------|
| **Análisis completado** | ✅ | G4 diagnóstico claro |
| **Riesgos evaluados** | ✅ | Muy bajo (UI pura) |
| **Microplan especificado** | ✅ | 11 secciones, lista |
| **Código preparado** | 🔴 | Pendiente autorización |
| **Compilación esperada** | ✅ | Alta confianza (UI changes) |
| **Validación esperada** | 🟡 | Depende de usuarios reales |

---

## SÍNTESIS DEL MICROPLAN

**Objetivo:** Jerarquía visual donde INPUT es protagonista.

**Cambios:**
- Eliminar: Title, explicación, headers números, espacios múltiples
- Cambiar: Input (90→120px, label visible), ejemplos (always visible)
- Mantener: Toda lógica de backend, routing, session state

**Riesgo:** Muy bajo (UI pura)

**Validación:** 4 tests. Métrica: 80%+ usuarios entienden sin leer.

**Próximo paso:** Autorización para implementar.

---

**FIN DEL MICROPLAN G4**

**Listo para:** Aprobación + Implementación
