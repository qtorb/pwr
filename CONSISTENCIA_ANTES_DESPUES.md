# CONSISTENCIA DE ESTADO: ANTES vs DESPUÉS

**Comparación de cómo se determina el estado de una tarea**

---

## ESCENARIO 1: Tarea Ejecutada Exitosamente

### ANTES: Inferencia Ambigua

```
Usuario crea tarea: "Análisis de vendedores"
  ↓
Usuario clica [Ejecutar]
  ↓
Router ejecuta con Gemini
  ↓
Output = "Análisis completo de 50 vendedores..."
  ↓ llm_output guardado en BD

PREGUNTA: ¿Cuál es el estado ahora?

Opción 1: ¿Tiene llm_output?
  → SÍ, tiene output → Debe estar ejecutada

Opción 2: ¿Qué dice status?
  → status = 'ejecutado' (campo UI)
  → Pero espera, ¿y si no se guardó bien?

Opción 3: ¿Qué ve el usuario en UI?
  → Ve un resultado
  → Pero... ¿está guardado? ¿Es real?

RESULTADO: ❓ Ambigüedad
```

### DESPUÉS: Explícito y Consistente

```
Usuario crea tarea: "Análisis de vendedores"
  ↓
Usuario clica [Ejecutar]
  ↓
Router ejecuta con Gemini
  ↓
Output = "Análisis completo de 50 vendedores..."
  ↓
BD: execution_status = 'executed'
  ↓

PREGUNTA: ¿Cuál es el estado?

RESPUESTA: execution_status = 'executed'
  → Guardado explícitamente en BD
  → Es la fuente de verdad
  → Todas las vistas lo leen

RESULTADO: ✅ Claridad
```

---

## ESCENARIO 2: Ejecución Fallida

### ANTES: ¿Qué Falló?

```
Usuario ejecuta tarea: "Email para cliente"
  ↓
Router intenta con OpenAI API
  ↓
❌ ERROR: API key inválida
  ↓

PREGUNTA: ¿Cuál es el estado ahora?

Opción 1: ¿Tiene llm_output?
  → NO → Debe estar sin ejecutar
  → Pero... ¿se intentó? ¿Falló?

Opción 2: ¿Qué dice status?
  → ¿'router_listo'? ¿'ejecutado'? ¿'error'?
  → No está claro

Opción 3: ¿Qué ve el usuario?
  → Error message rojo
  → Pero si recarga... ¿qué ve?

RESULTADO: ❌ Confusión
  - ¿Debería reintentar?
  - ¿O cambiar configuración?
  - ¿O crear una nueva tarea?
```

### DESPUÉS: Estado Explícito

```
Usuario ejecuta tarea: "Email para cliente"
  ↓
Router intenta con OpenAI API
  ↓
❌ ERROR: API key inválida
  ↓
BD: execution_status = 'failed'
BD: router_summary = "Error: API key inválida"
  ↓

PREGUNTA: ¿Cuál es el estado?

RESPUESTA: execution_status = 'failed'
  → Guardado explícitamente
  → render_task_state() muestra:
     "⚠️ Algo falló"
     "No se completó. Intenta de nuevo o ajusta la configuración."
     [⚡ Intentar de nuevo] [⚙️ Cambiar modo]

RESULTADO: ✅ Acción Clara
  - Usuario sabe qué pasó
  - Usuario sabe qué hacer
```

---

## ESCENARIO 3: Demo/Preview

### ANTES: ¿Es Real o Demo?

```
Usuario ejecuta tarea: "Propuesta de reportaje"
  ↓
Router intenta con Gemini
  ↓
⚠️ Sin credenciales de Google
  ↓
Fallback demo: Genera propuesta de ejemplo
  ↓
llm_output = "Propuesta de ejemplo..."
  ↓

PREGUNTA: ¿Es resultado real o demo?

Opción 1: ¿Tiene llm_output?
  → SÍ → Parece ejecutada
  → Pero... ¿es de verdad?

Opción 2: ¿Qué hay en router_summary?
  → Espera... ¿qué decía?
  → Debe revisar log

Opción 3: ¿Qué es esto en realidad?
  → Propuesta? ¿Resultado? ¿Demo?

RESULTADO: ❌ Incertidumbre
  - Usuario podría usar propuesta como resultado real
  - Riesgo de errores críticos
```

### DESPUÉS: Estado Diferenciado

```
Usuario ejecuta tarea: "Propuesta de reportaje"
  ↓
Router intenta con Gemini
  ↓
⚠️ Sin credenciales de Google
  ↓
Fallback demo: Genera propuesta de ejemplo
  ↓
BD: execution_status = 'preview'
BD: router_summary = "Propuesta previa (demo)..."
  ↓

PREGUNTA: ¿Es resultado real o demo?

RESPUESTA: execution_status = 'preview'
  → Guardado explícitamente
  → render_task_state() muestra:
     "📋 Propuesta lista"
     "El Router generó una propuesta. Revísala antes de decidir."
     [📋 Revisar]
  → router_summary dice: "Para resultado real: Conecta Google"

RESULTADO: ✅ Diferenciación Clara
  - Usuario ve que es DEMO, no resultado real
  - Usuario sabe qué hacer: conectar Google
  - No hay riesgo de confusión
```

---

## COMPARACIÓN TABULAR: ESTADO vs ACCIÓN

| Escenario | Antes | Después |
|-----------|-------|---------|
| **Tarea ejecutada** | ¿Tiene output? ✓ → Asumimos ejecutada | execution_status='executed' ✅ |
| **Tarea fallida** | ¿Qué pasó? ❓ Confuso | execution_status='failed' ✅ → Acciones claras |
| **Demo/Preview** | ¿Es real? ❓ Ambiguo | execution_status='preview' ✅ → "Esto es demo" |
| **Tarea nueva** | ¿Estado? ❓ Default? | execution_status='pending' ✅ → Claro |
| **Badge en Home** | Lógica compleja → Posibles errores | execution_status basado → Siempre correcto ✅ |
| **Botones en UI** | Derivados de lógica → A veces fallan | Basados en execution_status → Siempre contextuales ✅ |

---

## FLUJO DE ESTADO: ANTES vs DESPUÉS

### ANTES: Inferencia en Tiempo de Consulta

```
Usuario abre Home
  ↓
home_view() ejecuta
  ↓
get_recent_executed_tasks()
  ↓
Para cada tarea:
  - ¿Tiene llm_output? → SÍ/NO
  - ¿Cuándo se ejecutó? → Calcula timedelta
  - ¿Qué debe mostrar? → Lógica derivada
  ↓
determine_semantic_badge()
  ↓
❓ Múltiples puntos donde puede fallar la lógica
  ↓
Badge mostrado (¿correcto?)
```

### DESPUÉS: Lectura de Campo

```
Usuario abre Home
  ↓
home_view() ejecuta
  ↓
get_recent_executed_tasks()
  ↓
Para cada tarea:
  - Leer execution_status de BD
  - Leer updated_at
  ↓
determine_semantic_badge()
  ↓
✅ Lógica simple:
   - if execution_status == 'executed' AND tiempo < 1h:
     badge = "🔥 Recién generado"
  ↓
Badge mostrado (correcto, siempre)
```

---

## CONFIABILIDAD

### ANTES: Depende de Lógica

```
¿Cuándo falla la lógica?

1. Si llm_output fue guardado pero status no
2. Si status se salvó pero llm_output no
3. Si status cambió pero BD no se actualizó bien
4. Si router_summary es incompleto
5. Si hay race condition en guarda paralela

RESULTADO: Bugs posibles, difíciles de debuggear
```

### DESPUÉS: Depende de Campo Explícito

```
¿Cuándo falla?

1. Nunca - execution_status es atómico en BD
2. Backfill inicial lo llena de valores correctos
3. Cada operación lo actualiza explícitamente
4. Views simplemente lo leen

RESULTADO: 100% confiable, fácil de debuggear
```

---

## SCENARIO: Bug Report "Estado incorrecto en Home"

### ANTES: Investigación Compleja

```
Bug: "Ayer ejecuté una tarea, hoy en Home no aparece como completada"

Debugging necesario:
1. ¿Tiene llm_output? → SELECT llm_output FROM tasks WHERE id=X
2. ¿Qué es status? → SELECT status FROM tasks WHERE id=X
3. ¿Cuándo se ejecutó? → SELECT updated_at FROM tasks WHERE id=X
4. ¿Qué dice router_summary? → SELECT router_summary FROM tasks WHERE id=X
5. ¿Qué calcula determine_semantic_badge()? → Run function
6. ¿Por qué falla? → Revisar lógica complejita

RESULTADO: 30 minutos de debugging
```

### DESPUÉS: Investigación Simple

```
Bug: "Ayer ejecuté una tarea, hoy en Home no aparece como completada"

Debugging necesario:
1. SELECT execution_status FROM tasks WHERE id=X
2. Ver qué devuelve render_task_state()

RESULTADO: 2 minutos de debugging

¿Si está mal? → Check en qué punto se guardó mal execution_status
```

---

## CONCLUSIÓN

### Opción B: execution_status en BD

✅ **Consistencia Garantizada**
- Un campo = una verdad
- No hay múltiples fuentes de verdad conflictivas

✅ **Confiabilidad**
- Estado guardado explícitamente
- Backfill automático
- Imposible tener estado ambiguo

✅ **Mantenibilidad**
- Fácil de debuggear
- Lógica simple (lectura de campo)
- Menos bugs

✅ **UX Confiable**
- UI siempre muestra estado correcto
- Botones siempre contextuales
- Badges siempre relevantes

---

**Antes**: Estado inferido, ambiguo, propenso a bugs
**Después**: Estado explícito, confiable, garantizado

🎯 **Objetivo alcanzado: Eliminar inconsistencias entre estado visual, estado real y datos persistidos**
