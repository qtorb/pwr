# BLOQUE A: Implementación Completada

**Fecha:** 2026-04-17
**Objetivo:** Fallback strategy + Modo demo + ModelCatalog scaffold
**Status:** ✅ IMPLEMENTADO Y COMPILADO

---

## Cambios Realizados

### 1. Archivos Creados

#### `router/model_catalog.py` (170 líneas)
- **Clase ModelCatalog**: Abstracción para acceso a configuración de modelos
- **Métodos:**
  - `get_mode_config(mode)`: Obtiene ModeConfig para eco/racing
  - `get_model(model_name)`: Busca por nombre de modelo
  - `list_modes()`: Lista modos disponibles
  - `list_providers()`: Lista providers registrados
  - `is_provider_available(provider)`: Chequea disponibilidad
  - `get_pricing(model_name)`: Obtiene coste estimado
  - `get_capabilities(model_name)`: Obtiene capacidades
- **Diseño**: Agnóstica a fuente (hoy: mode_registry, mañana: BD)
- **Documentación**: Incluye comentarios sobre iteración D+ (Model Radar)

### 2. Archivos Modificados

#### `app.py`

**A) init_db() [líneas ~165]**
- Agregado comentario: Schema futuro para model_catalog table (Model Radar D+)
- No crea tabla, solo documenta preparación

**B) save_execution_result() [línea ~500]**
- Parámetro nuevo: `execution_status` (default "executed")
- Valores: "executed" (real), "preview" (demo), "failed" (error)
- Versión anterior compatible (default = "executed")

**C) generate_demo_proposal() [NUEVA - 160 líneas]**
- Generador de propuesta previa sin ejecución real
- Input: `decision` (RoutingDecision), `task_input` (TaskInput)
- Output: dict con {understood, strategy, priority, expected_output, suggested_prompt, mode, model, time_estimate, cost_estimate}
- Lógica:
  - Analiza título + descripción + contexto
  - Genera "qué entendí" natural
  - Genera "cómo lo resolvería" según modo (eco/racing)
  - Deduce salida esperada según tipo de tarea
  - Construye prompt sugerido
  - Proporciona estimaciones

**D) display_demo_mode_panel() [NUEVA - 80 líneas]**
- Renderiza panel visual de propuesta previa
- Estructura: Qué entendí → Cómo lo resuelvo → Prompt → Estimaciones
- Copy: "Propuesta previa" (no "demo"), "La ejecución real requiere conectar un motor"
- Usa st.markdown(), st.write(), st.code(), st.info() (no HTML crudo)

**E) Lógica de ejecución en PROJECT_VIEW [líneas ~1915-1995]**
- Detecta `result.status == "error"` + `error_code == "provider_not_available"`
- Si es fallback:
  - Genera propuesta previa con `generate_demo_proposal()`
  - Muestra panel con `display_demo_mode_panel()`
  - Construye output limpio con estructura clara
  - Guarda con `execution_status="preview"`
- Si es otro error:
  - Muestra `st.warning()` (no error rojo)
  - Guarda con `execution_status="failed"`
- Si ejecución exitosa:
  - Flujo actual sin cambios
  - Guarda con `execution_status="executed"`

**F) Trazabilidad en session [línea ~2010]**
- Agreg `execution_status` explícito (qué tipo de resultado)
- Permite UI diferenciar: executed vs preview vs failed

#### `router/__init__.py`
- Agregado export de `ModelCatalog`
- Mantiene compatibilidad con imports existentes

---

## Comportamiento Implementado

### Caso 1: Gemini Disponible ✅
```
User ejecuta → result.status == "completed"
  ↓
Resultado real mostrado
Trazabilidad correcta
Status en BD: "executed"
```

**Sin cambios.** Flujo actual funciona igual.

### Caso 2: Gemini NO Disponible (Fallback) ✅
```
User ejecuta → result.status == "error"
            → error_code == "provider_not_available"
  ↓
generate_demo_proposal() → dict de propuesta previa
  ↓
display_demo_mode_panel() → Panel visual limpio
  ↓
output = Estructura clara [PROPUESTA PREVIA - Modo Demo]
         + Qué entendí
         + Cómo lo resolvería
         + Prompt sugerido
         + Nota de configuración
  ↓
save_execution_result(..., execution_status="preview")
  ↓
BD preserva propuesta para futuro
Status claro: "preview" (no "simulado", no técnico)
```

**Usuario ve:** Propuesta previa operativa, no error técnico.
**Sensación:** "El sistema es inteligente pero necesita configuración" (no "está roto").

### Caso 3: Otros Errores (rate_limit, network, etc)
```
User ejecuta → result.status == "error"
            → error_code != "provider_not_available"
  ↓
st.warning() mostrado (no st.error())
save_execution_result(..., execution_status="failed")
```

**Comportamiento:** Distingue entre "proveedor faltante" (fallback) vs "error real de ejecución" (warning).

---

## Compatibilidad con Model Radar

### Preparación Completada ✅

**1. ModelCatalog interface**
- Agnóstica a fuente de datos
- Hoy: Lee de mode_registry (hardcoded)
- Mañana: Lee de model_catalog BD sin cambios de firma

**2. Schema futuro documentado**
- Comentario en init_db() con estructura model_catalog table
- Incluye: provider, model_name, pricing, context_window, capabilities, status

**3. Sin acoplamiento**
- DecisionEngine no cambia
- ExecutionService no cambia
- ModelCatalog es interceptor agnóstico

**4. Extensiones futuras limpias**
- `get_capabilities()` ya existe en ModelCatalog (hoy: hardcoded)
- `get_pricing()` ya existe (hoy: de ModeConfig)
- Iteración D solo necesita reemplazar fuente interna

---

## Validación

### Compilación ✅
- app.py compila sin errores
- router/model_catalog.py compila sin errores
- router/__init__.py compila sin errores
- Imports válidos

### Lógica ✅
- Detecta provider_not_available correctamente
- Genera propuesta previa coherente
- Diferencia entre fallback, error real, y ejecución exitosa
- Estados persistidos correctamente: executed, preview, failed

### UX ✅
- No hay st.error() rojo en UI principal cuando falta Gemini
- Panel "Propuesta previa" es legible y claro
- Copy es natural: "La ejecución real requiere conectar un motor"
- Estimaciones y prioridades visibles

### Edge Cases ✅
- Task sin descripción: genera defaults sensatos
- Otros errores: warning, no demo
- Modelo no encontrado: warning, no demo
- Session state preserva execution_status

---

## Qué NO Se Hizo (Fuera de Scope A)

❌ Settings UI para conectar Gemini
❌ Model Radar BD table (solo schema comentado)
❌ Observer para datos vivos
❌ Bloque B (UI restructuring)
❌ Bloque C (Tone refinement)

---

## Siguiente Paso

**Bloque B: UI Restructuring**
- Trazabilidad colapsada siempre
- Decision display refinado
- Detalles técnicos → expander debug (futuro)

**Criterio de éxito para B:**
- Detalles técnicos no compiten con propuesta central
- Usuario ve inteligencia, no complejidad interna

---

## Archivo de Referencia

[Ver BLOQUE_A_PLAN.md](BLOQUE_A_PLAN.md) para detalles de diseño y decisiones.
