# BLOQUE A: Plan de Implementación Detallado
## Fallback Strategy + Modo Demo + ModelCatalog Scaffold

**Objetivo:** Cuando no hay Gemini disponible, mostrar propuesta previa útil (modo demo) en lugar de error técnico. Preparar arquitectura para futuro Model Radar.

**Alcance:** Comportamiento + UI + Interfaz (no implementación de DB ni Observer)

**Esfuerzo estimado:** 4-5 horas incluida ModelCatalog scaffold

---

## 1. ARCHIVOS EXACTOS A TOCAR

### Crear (nuevos)
```
router/model_catalog.py          (interfaz scaffold, ~60 líneas)
BLOQUE_A_IMPLEMENTATION.md       (historial de cambios - opcional)
```

### Modificar (existentes)
```
router/mode_registry.py          (wrappear en ModelCatalog)
router/execution_service.py      (lógica de detección provider)
app.py                           (nueva función generate_demo_proposal)
app.py                           (cambiar ejecución: si error → demo)
app.py                           (cambiar UI: st.error → demo panel)
```

### NO tocar
```
router/decision_engine.py        (sin cambios)
router/domain.py                 (sin cambios)
router/providers.py              (sin cambios)
app.py init_db()                 (solo comentarios, no schema nuevo)
```

---

## 2. FLUJO ACTUAL VS. FLUJO NUEVO

### Flujo Actual (ROTO)

```
User abre tarea en PROJECT_VIEW
    ↓
User pulsa "Ejecutar"
    ↓
show_progress_messages() (Analizando...)
    ↓
result = execution_service.execute(task_input)
    ↓
if result.status == "error":
    st.error(f"Error: {result.error.message}")  ❌ TÉCNICO, ROTO
    ↓
    router_summary = "Intento fallido..."
    save_execution_result(...)
    st.rerun()
```

**Problema:** Si Gemini no disponible, ExecutionError con mensaje técnico aparece prominente.

---

### Flujo Nuevo (ARREGLADO)

```
User abre tarea en PROJECT_VIEW
    ↓
User pulsa "Ejecutar"
    ↓
show_progress_messages() (Analizando...)
    ↓
result = execution_service.execute(task_input)
    ↓
if result.status == "error":
    error_code = result.error.code

    if error_code == "provider_not_available":  ✅ DETECTAR FALLBACK
        ↓
        demo_proposal = generate_demo_proposal(
            decision=result.routing,
            task_input=task_input
        )
        ↓
        display_demo_mode_panel(demo_proposal)  ✅ PROPUESTA ÚTIL
        ↓
        router_summary = "Propuesta simulada..."
        save_execution_result(demo_proposal)
        st.rerun()

    else:  # Otros errores (network, rate_limit, etc)
        st.warning(f"Error de ejecución: {result.error.message}")
        # Mostrar warning, no error
```

**Mejora:** Si Gemini no disponible, mostramos propuesta simulada (inteligencia visible).

---

## 3. COMPORTAMIENTO CON PROVIDER DISPONIBLE

**Caso:** GEMINI_API_KEY está configurada y válida

```
User escribe tarea
    ↓
Display decision previa ✅ (feature existente)
    ↓
User pulsa "Generar propuesta" → tarea creada ✅
    ↓
User pulsa "Ejecutar" en resultado
    ↓
ExecutionService.execute():
  - DecisionEngine.decide() → RoutingDecision ✅
  - GeminiProvider inicializado → ✅
  - provider.run() → respuesta real ✅
    ↓
result.status == "completed" ✅
    ↓
Mostrar resultado real, trazabilidad, botones
```

**SIN cambios.** El flujo actual funciona.

---

## 4. COMPORTAMIENTO SIN PROVIDER DISPONIBLE

**Caso 1:** GEMINI_API_KEY no existe o invalida

```
User escribe tarea
    ↓
Display decision previa ✅ (feature existente)
  "Modo recomendado: ECO (rápido)"
  "Motivo: tarea..."
  "Tiempo: ~2-4s, Coste: bajo"
    ↓
User pulsa "Generar propuesta" → tarea creada ✅
    ↓
User pulsa "Ejecutar" en resultado
    ↓
ExecutionService.execute():
  - DecisionEngine.decide() → RoutingDecision ✅
  - GeminiProvider initialization → ❌ ValueError("GEMINI_API_KEY no configurada")
  - ExecutionService catch → ExecutionError(code="provider_not_available", message="...")
    ↓
result.status == "error"
result.error.code == "provider_not_available"
    ↓
detect_fallback() → TRUE
    ↓
generate_demo_proposal(
    decision=result.routing,
    task_input=task_input
)
    ↓
Retorna:
  {
    "understood": "Quieres un resumen breve de este documento en 3 ideas clave",
    "strategy": "Lo abordaría de forma rápida, extrayendo las ideas principales",
    "priority": "velocidad y claridad",
    "expected_output": "resumen en 3 puntos",
    "suggested_prompt": "Resume el documento en 3 ideas clave...",
    "mode": "eco",
    "model": "gemini-2.5-flash-lite",
    "time_estimate": "~2–4s",
    "cost_estimate": "bajo"
  }
    ↓
display_demo_mode_panel(demo_proposal)
    ↓
save_execution_result(
  llm_output="[MODO DEMO]\n" + demo_proposal.understood + ...
  router_summary="Propuesta simulada (ECO)..."
)
    ↓
User ve: ✨ Propuesta previa + Modo demo activo
```

**Caso 2:** API key válida pero modelo discontinuado/unavailable

```
ExecutionService:
  - GeminiProvider inicializado ✅
  - provider.run() → Exception("Model not found")
  - ExecutionError(code="model_not_found", ...)
    ↓
if error_code == "model_not_found":
    → Mostrar warning: "Modelo no disponible, intenta configurar otro"
    → NO usar demo (es un error diferente)
```

**Comportamiento:** Warning, no demo (es error de configuración, no de provider faltante).

---

## 5. ESTRUCTURA UX DEL MODO DEMO

### Panel "Propuesta Previa" (Nuevo)

**Concepto visible (NO "demo"):**
- Título: "Propuesta previa" o "Vista previa del Router"
- Aclaración: "La ejecución real requiere conectar un motor"
- Percepción: preview operativa del sistema, no demo vacía

```
┌─────────────────────────────────────────────────┐
│ ✨ Propuesta previa                             │
│ La ejecución real requiere conectar un motor    │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ 🧠 Qué he entendido                             │
│ ─────────────────────────────────────────────── │
│ Quieres un resumen breve de este documento      │
│ en 3 ideas clave, con una salida clara          │
│ y fácil de revisar.                             │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ 🎯 Cómo lo resolvería                           │
│ ─────────────────────────────────────────────── │
│ Lo abordaría de forma rápida, extrayendo las    │
│ ideas principales y devolviéndolas en 3 puntos  │
│ claros y ordenados.                             │
│                                                 │
│ Prioridad: velocidad y claridad                 │
│ Salida esperada: resumen en 3 puntos            │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ 💬 Prompt sugerido                              │
│ ─────────────────────────────────────────────── │
│ Resume el documento en 3 ideas clave.           │
│ Escribe una respuesta breve, clara y sin        │
│ repeticiones.                                   │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ Para generar el resultado real:                 │
│ [ Activar ejecución real ]                      │
│ Configúralo en Settings                         │
└─────────────────────────────────────────────────┘
```

### Componentes en app.py

```python
def display_demo_mode_panel(demo_proposal: dict):
    """
    Muestra propuesta previa en modo demo.

    Args:
        demo_proposal: dict con keys:
            - understood: str (qué entendió)
            - strategy: str (cómo lo resolvería)
            - priority: str (prioridad)
            - expected_output: str (salida esperada)
            - suggested_prompt: str (prompt)
            - mode: str (eco/racing)
            - model: str (gemini-2.5-flash-lite, etc)
            - time_estimate: str (~2-4s)
            - cost_estimate: str (bajo/medio-alto)
    """
    st.container()
    st.markdown("### ✨ Propuesta previa")
    st.caption("Modo demo activo · La ejecución real requiere conectar un motor")

    st.write("")
    st.markdown("### 🧠 Qué he entendido")
    st.write(demo_proposal["understood"])

    st.write("")
    st.markdown("### 🎯 Cómo lo resolvería")
    st.write(demo_proposal["strategy"])
    st.caption(f"**Prioridad:** {demo_proposal['priority']}")
    st.caption(f"**Salida esperada:** {demo_proposal['expected_output']}")

    st.write("")
    st.markdown("### 💬 Prompt sugerido")
    st.code(demo_proposal["suggested_prompt"], language="text")

    st.write("")
    st.markdown("**Para generar el resultado real:**")
    col1, col2 = st.columns([0.7, 0.3])
    with col1:
        st.info("Configúralo en Settings (futuro) o conecta Gemini en .env")
```

---

## 6. INTRODUCIR ModelCatalog SIN SOBRECOMPLICAR A

### Principio: Abstracción de Catálogo, Agnóstica a Fuente

**Hoy (Bloque A):** Implementación estática (mode_registry)
**Mañana (Model Radar D+):** Implementación dinámica (observatorio BD)
**Costura:** Interfaz ModelCatalog es agnóstica a fuente

```python
# router/model_catalog.py (NUEVO - 60 líneas)

from .mode_registry import MODE_REGISTRY, ModeConfig
from typing import List, Optional

class ModelCatalog:
    """
    Abstracción para catálogo y configuración de modos/modelos.

    Hoy (Bloque A):
    - Implementación estática: Lee de mode_registry.py
    - Mapeo fijo: eco → flash-lite, racing → pro

    Mañana (Model Radar D+):
    - Implementación dinámica: Lee de modelo_catalog BD
    - Observador actualiza precios, capacidades, estado
    - Interfaz NO cambia (agnóstica a fuente)

    Beneficio: DecisionEngine, ExecutionService, app.py no necesitan refactor cuando Model Radar llegue.
    """

    def __init__(self):
        """Inicializa catálogo (hoy desde mode_registry, mañana desde BD)."""
        self._catalog = MODE_REGISTRY  # Hoy: hardcoded

    def get_mode_config(self, mode: str) -> ModeConfig:
        """
        Obtiene configuración de un modo.

        Args:
            mode: "eco" o "racing"

        Returns:
            ModeConfig con provider, model, pricing, etc

        Raises:
            ValueError si modo no existe
        """
        if mode not in self._catalog:
            raise ValueError(f"Modo no soportado: {mode}")
        return self._catalog[mode]

    def get_model(self, model_name: str) -> Optional[ModeConfig]:
        """
        Busca configuración por nombre de modelo.

        Returns:
            ModeConfig si existe, None si no.

        Futuro: Usará búsqueda en BD
        """
        for config in self._catalog.values():
            if config.model == model_name:
                return config
        return None

    def list_modes(self) -> List[str]:
        """Retorna lista de modos disponibles."""
        return list(self._catalog.keys())

    def is_provider_available(self, provider: str) -> bool:
        """
        Chequea si proveedor está disponible.

        Hoy: Hardcoded (sempre True)
        Mañana: Chequea BD observatorio
        """
        # TODO: Implementar chequeo dinámico en iteración E (Model Radar)
        return provider in ["gemini", "mock"]
```

### Cambios Mínimos en Otros Módulos

**En mode_registry.py:** Sin cambios
- Mantener MODE_REGISTRY igual
- ModelCatalog solo lo wrappea

**En execution_service.py:** Sin cambios en lógica
```python
# Hoy:
from .mode_registry import get_mode_config
config = get_mode_config(mode)

# Después de A:
from .model_catalog import ModelCatalog
catalog = ModelCatalog()
config = catalog.get_mode_config(mode)
# Siguen devolviendo lo mismo
```

**En app.py:** Sin cambios, excepto nueva función generate_demo_proposal()

### Ventaja de esto

- ✅ ModelCatalog es "listo para recibir BD" sin refactor
- ✅ Cuando Model Radar esté, solo cambia `__init__` de ModelCatalog
- ✅ DecisionEngine sigue agnóstico
- ✅ ExecutionService sigue agnóstico
- ✅ No hay sobre-ingeniería hoy

---

## 7. RIESGOS Y EDGE CASES

### Edge Case 1: GeminiProvider inicializa bien, pero modelo específico falla en run()

```
Scenario:
- GEMINI_API_KEY válida ✅
- Cliente Gemini conecta ✅
- Pero gemini-2.5-flash-lite no existe o está deprecated

Hoy:
- provider.run() lanza Exception
- ExecutionService clasifica → "model_not_found"
- Se muestra st.warning(), no demo

Correcto:
- model_not_found NO es fallback
- Es error de configuración
- Usuario debe actualizar mode_registry
```

**Manejo:** `if error_code == "provider_not_available"` solamente. Los demás errores → warning.

### Edge Case 2: Usuario intenta ejecutar con preferred_mode="racing" pero MockEcoProvider es fallback

```
Scenario:
- Gemini falla
- DecisionEngine decide → RACING
- Pero fallback es MockEcoProvider (eco solo)

Hoy:
- MockEcoProvider.run() devuelve respuesta eco
- Pero reasoning_path dice "RACING"
- Inconsistencia

Solución:
- demo_proposal['mode'] debe reflejar lo que HUBIERA ejecutado
- No lo que el mock genera
- UI dice: "Cómo lo RESOLVERÍA (si Gemini)" no "cómo lo resuelve el mock"
```

**Manejo:** generate_demo_proposal() usa decision.mode, no intenta ejecutar mock.

### Edge Case 3: Task sin descripción, solo título

```
Scenario:
- User escribe: "resume esto"
- Sin contexto
- Sin descripción en tareas

Hoy:
- DecisionEngine.decide() analiza title + description + context
- Puede dar reasoning path muy corto
- demo_proposal['strategy'] puede quedar vacía

Solución:
- generate_demo_proposal() verifica no-vacío
- Si vacío, usa default genérico: "Usaré análisis directo del contenido"
```

**Manejo:** Defaults en generate_demo_proposal() para campos vacíos.

### Edge Case 4: Usuario hace clic en "Ejecutar" 2+ veces rápido

```
Scenario:
- User pulsa "Ejecutar"
- Se muestra progreso
- User pulsa de nuevo antes de que termine

Hoy:
- Streamlit rerun puede causar doble ejecución
- Se guarda 2x en BD

Solución:
- Usar bandera session_state para bloquear durante ejecución
- `st.button(..., disabled=True)` mientras se ejecuta
```

**Manejo:** Ya existe con progreso_placeholder, mantener como está.

### Edge Case 5: Mode Radar vive en DB separada vs. misma DB

```
Future scenario:
- Si Model Radar está en BD separada (observatorio.db)
- ModelCatalog debe conectar a ambas BDs
- Potencial conflicto de transacciones

Solución:
- ModelCatalog no toca BD (lee solo, stateless)
- Cuando Model Radar se implemente, será read-only desde aquí
- Observador actualiza DB aparte
```

**Preparación:** Documentar en model_catalog.py que es read-only.

---

## 8. CRITERIOS DE VALIDACIÓN

### Funcional

- [ ] Cuando Gemini disponible:
  - [ ] Ejecución normal funciona
  - [ ] Resultado real aparece
  - [ ] Trazabilidad correcta
  - [ ] Sin cambios visuales

- [ ] Cuando Gemini NO disponible:
  - [ ] No hay st.error() rojo en UI principal
  - [ ] Panel "Propuesta previa" aparece (concepto: preview operativa, no demo)
  - [ ] Propuesta incluye: qué-entendí, cómo-lo-resuelvo, prompt, estimaciones
  - [ ] Texto dice "La ejecución real requiere conectar un motor" (no "demo")
  - [ ] Resultado se guarda en BD con status="preview" (claro, no "simulado")

- [ ] Edge cases:
  - [ ] Otro tipo de error (rate_limit, network) → st.warning(), no demo
  - [ ] modelo_not_found → warning, no demo
  - [ ] Task vacía → demo proporciona defaults sensatos
  - [ ] Double-click execute → deshabilitado durante progreso

### UX

- [ ] Panel demo es legible (no HTML crudo)
- [ ] Estructura clara: 4 bloques + CTA
- [ ] Copy natural, sin tecnicismos
- [ ] Botones/CTAs accesibles

### Arquitectura (Model Radar prep)

- [ ] ModelCatalog interface existe
- [ ] mode_registry wrappedo (sin cambios funcionales)
- [ ] DecisionEngine sin cambios
- [ ] ExecutionService sin cambios
- [ ] init_db() tiene comentario sobre future model_catalog table
- [ ] model_catalog.py documenta "listo para DB en iteración E"

### Regresión

- [ ] Home view sigue funcionando (tiene decision_previa feature)
- [ ] Project view execution sigue funcionando
- [ ] Mejorar (RACING mode) sigue funcionando
- [ ] Guardar activos sigue funcionando
- [ ] Expandibles (Ficha, Prompt, Trazabilidad) siguen colapsados
- [ ] No hay cambios en BD schema (solo comentarios)

---

## 9. COMPATIBILIDAD CON MODEL RADAR / OBSERVATORIO

### Qué prepamos en A para facilitar D+

#### 1. Interfaz ModelCatalog (creada en A)
```
Iteración A:  ModelCatalog + mode_registry wrapper
              (fuente = hardcoded)

Iteración D:  Agregar model_catalog table a BD
              (fuente = BD)

Iteración E:  ModelCatalog.get_mode_config() lee de BD
              No cambia signature, solo fuente

Iteración F:  Observer llena model_catalog table con datos vivos
              ModelCatalog lee datos actuales automáticamente
```

Sin preparación en A: Habría que refactorizar DecisionEngine en D.
Con preparación en A: Solo cambio interno de ModelCatalog.

#### 2. Comentarios en init_db()
```python
# En app.py init_db(), agregar comentario:
"""
FUTURO: Model Radar (iteración D)
Model Catalog table para observatorio vivo.
Cuando esté listo, agregar aquí:

CREATE TABLE IF NOT EXISTS model_catalog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,              -- "gemini", "claude", etc
    model_name TEXT UNIQUE NOT NULL,     -- "gemini-2.5-flash-lite", etc
    pricing_input_per_mtok REAL,         -- $0.000075
    pricing_output_per_mtok REAL,        -- $0.0003
    context_window INTEGER,              -- 1000000
    capabilities_json TEXT DEFAULT '{}', -- {"vision": true, "reasoning": false}
    status TEXT DEFAULT 'active',        -- "active", "deprecated", "limited"
    deprecated_at TEXT,                  -- ISO timestamp
    updated_at TEXT NOT NULL,            -- Cuándo fue actualizado
    FOREIGN KEY(provider) REFERENCES model_providers(name)
)

Será leído por ModelCatalog.
Observer lo actualiza periódicamente.
"""
```

#### 3. Documentación en model_catalog.py
```python
class ModelCatalog:
    """
    Interface para acceso a modelos.

    PRESENTE (Bloque A):
    - Lee de mode_registry.py (hardcoded)
    - Interfaz estable, agnóstica a fuente

    FUTURO (Iteración D+):
    - Leerá de BD model_catalog cuando esté lista
    - Observer poblará datos vivos (pricing, capacidades, estado)
    - Sin cambios en signature pública

    FUTURO (Iteración E):
    - DecisionEngine v2 usará datos vivos
    - Decisiones basadas en pricing/capacidades actuales

    FUTURO (Iteración F):
    - Public /radar API expondrá estos datos
    """
```

#### 4. Qué NO hacer en A
- ❌ No crear tabla model_catalog (es herencia huérfana)
- ❌ No implementar Observer (es futuro D/E)
- ❌ No cambiar DecisionEngine (seguirá agnóstico)
- ❌ No agregar BD queries a ExecutionService
- ❌ No hardcodear más lógica (wrappear lo que existe)

#### 5. Qué sí hacer en A
- ✅ Crear ModelCatalog interface
- ✅ Wrappear mode_registry (sin cambiar lógica)
- ✅ Documentar puntos futuros
- ✅ Comentar schema futuro
- ✅ Mantener CERO dependencia en BD

---

## 10. ORDEN DE IMPLEMENTACIÓN (Secuencial)

### Paso 1: Crear ModelCatalog (router/model_catalog.py)
- Interfaz para get_mode_config(), get_model(), list_modes()
- Fuente = mode_registry hoy
- Completamente agnóstica a donde venga data

**Chequeo:**
- [ ] Imports OK
- [ ] Métodos funcionan
- [ ] Retorna ModeConfig igual que antes

### Paso 2: Actualizar mode_registry.py
- Wrapar en ModelCatalog
- Cambiar imports en otros módulos si es necesario
- Mantener signature exacta igual

**Chequeo:**
- [ ] get_mode_config("eco") retorna igual
- [ ] get_mode_config("racing") retorna igual
- [ ] Errores igual que antes

### Paso 3: Crear generate_demo_proposal()
- Nueva función en app.py
- Input: decision (RoutingDecision), task_input (TaskInput)
- Output: dict con understood, strategy, prompt, etc.

**Chequeo:**
- [ ] Genera texto coherente
- [ ] No confunde modo (eco vs racing)
- [ ] Handles campos vacíos (defaults)
- [ ] Copy es natural, no técnico

### Paso 4: Crear display_demo_mode_panel()
- Nueva función en app.py
- Input: demo_proposal (dict)
- Output: nada, solo st.markdown/st.write/st.code

**Chequeo:**
- [ ] Renderiza sin errores
- [ ] Estructura clara
- [ ] Copy legible
- [ ] No HTML crudo

### Paso 5: Cambiar lógica ejecución en PROJECT_VIEW
- En línea ~1705-1780 (donde está if execute_btn)
- Detectar si result.status == "error" y error_code == "provider_not_available"
- Llamar generate_demo_proposal()
- Llamar display_demo_mode_panel()
- Guardar resultado con flag "simulado"

**Chequeo:**
- [ ] Flujo sin error técnico
- [ ] Demo propuesta aparece
- [ ] Trazabilidad se guarda
- [ ] Otros errores → warning (no demo)

### Paso 6: Agregar comentarios Model Radar
- En init_db(): comentario sobre future model_catalog table
- En model_catalog.py: docstring sobre futuro
- En BLOQUE_A_PLAN.md o README: referencia a Model Radar prep

**Chequeo:**
- [ ] Comentarios claros
- [ ] Schema futuro documentado
- [ ] No hay código de Model Radar aquí

---

## DEPENDENCIAS Y ORDEN

```
ModelCatalog (paso 1)
    ↓
wrappear mode_registry (paso 2)
    ↓
generate_demo_proposal + display_panel (pasos 3-4)
    ↓
cambiar ejecución (paso 5)
    ↓
comentarios (paso 6)
```

**No hay ejecución posible de paso N sin pasos 1-N-1.**

---

## STATUS TECH

### Objetivo actual
Implementar fallback strategy: cuando no hay Gemini, mostrar propuesta simulada útil (modo demo) en lugar de error técnico. Preparar arquitectura (ModelCatalog) para futuro Model Radar sin sobrecomplicar.

### Hecho
✅ Diagnóstico técnico completeto (TECH_AUDIT.md)
✅ Identificación de problema (provider no disponible rompe UX)
✅ Decisiones tomadas (modo demo explícito, A → B → C, ModelCatalog prep)
✅ Plan detallado escrito (este documento)

### En progreso
⏳ Validación del plan (espera de Albert)

### Bloqueadores / riesgos
- 🔴 **SIN** Plan de implementación: Alto riesgo de scope creep
- 🔴 **SIN** validación: Podría haber malinterpretación de algo
- ⚠️ Error handling complexity: Muchos edge cases, pero manejables

### Siguiente paso
**Espera validación de Albert:**
1. ¿Plan es correcto?
2. ¿Estructura UX demo es aceptable?
3. ¿Preparación ModelCatalog está bien?
4. ¿Algún punto a ajustar?

Una vez validado → pasar a **IMPLEMENTACIÓN del Bloque A**

### Decisión que necesito de Albert
1. ¿Plan de implementación es correcto? ¿Algo a ajustar?
2. ¿Estructura UX del demo es lo que imaginabas?
3. ¿Esfuerzo/alcance OK (4-5 horas)?
4. ¿Autorizo seguir a implementación?

---

**LÍNEA CLARA:** Plan prepara Bloque A sin encorsetar Model Radar. DecisionEngine sigue agnóstico. ExecutionService sin cambios de firma. ModelCatalog es escalera hacia BD. Todo reversible si es necesario.
