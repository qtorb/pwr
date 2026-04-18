# TECH AUDIT: Portable Work Router

## 1. INVENTARIO DE LO DESARROLLADO

### Estructura Física
```
PWR_repo/
├── app.py                          (2169 líneas, UI principal)
├── router/                         (módulo ejecutable)
│   ├── __init__.py
│   ├── domain.py                   (dataclasses: TaskInput, RoutingDecision, etc)
│   ├── decision_engine.py          (lógica de decisión eco/racing)
│   ├── execution_service.py        (orquestador: decide → resolve → execute)
│   ├── providers.py                (GeminiProvider, MockEcoProvider, MockRacingProvider)
│   ├── metadata_builder.py         (construcción de métricas)
│   ├── mode_registry.py            (configuración de modos)
│   └── __pycache__/                (caché de bytecode)
├── pwr_data/                       (base de datos sqlite)
│   └── pwr.db
├── .env.example                    (template de configuración)
└── [documentación, backups, zips]
```

### Base de Datos (SQLite)
**Tablas implementadas:**
- `projects` (13 columnas): Metadatos de proyectos, slug, favoritos
- `project_documents` (9 columnas): Documentos uploadados por proyecto
- `tasks` (14 columnas): Tareas, contexto, outputs, results
- `assets` (7 columnas): Activos reutilizables guardados

**Integridad:**
- ✅ Foreign keys correctas
- ✅ Migrate logic con `ensure_column()` para evolución de schema
- ✅ Sample data: 2 proyectos por defecto (PWR, RosmarOps)

### Módulos Python (router/)

#### **domain.py** (52 líneas)
**Implementado:**
- `TaskInput`: dataclass con task_id, title, description, task_type, context, project_name, max_budget, preferred_mode
- `RoutingDecision`: mode, provider, model, reasoning_path, complexity_score
- `ExecutionMetrics`: latency_ms, estimated_cost, provider_used, model_used
- `ExecutionError`: code, message
- `ExecutionResult`: status (completed/error), output_text, routing, metrics, error

**Estado:** ✅ Completo y funcional

#### **decision_engine.py** (80 líneas)
**Lógica:**
- Analiza `title + description + context` como combined text
- Señales detectadas: task_type, volumen de contexto, términos estratégicos, términos técnicos
- Score: 0.0-1.0
- Decisión: eco si score < 0.5, racing si >= 0.5
- Respeta `preferred_mode` (override de usuario)

**Reasoning path:** Detallado, incluye señales detectadas y criterio

**Estado:** ✅ Funcional pero reasoning_path es técnico (detalle backend)

#### **execution_service.py** (129 líneas)
**Orquestación:**
1. Decide (DecisionEngine)
2. Resuelve provider (por nombre)
3. Ejecuta provider.run()
4. Construye ExecutionResult

**Error handling:**
- ✅ Intenta inicializar GeminiProvider, guarda error si falla
- ✅ Fallback a Mock provider disponible
- ✅ Captura errores de provider, clasifica, devuelve ExecutionError explícito

**Estado:** ✅ Sólido, manejo de errores correcto en arquitectura

#### **providers.py** (188 líneas)
**GeminiProvider:**
- ✅ Valida API key al init
- ✅ Valida conexión
- ✅ Valida modelos esperados (flash-lite, pro)
- ✅ Construcción de prompt desde TaskInput
- ✅ Clasificación de excepciones (invalid_key, rate_limit, network, model_not_found, provider_error)
- ✅ Fallback a mock si falla

**MockEcoProvider:**
- ✅ Simula respuesta rápida (0.6s sleep)
- ✅ Genera output ficticio coherente

**MockRacingProvider:**
- ⚠️ Existe pero NO se usa en code. ExecutionService solo registra MockEcoProvider.
- ✅ Simula respuesta profunda (1.4s sleep)

**Estado:** ✅ GeminiProvider robusto, Mock providers parcialmente usado

#### **metadata_builder.py** (estado)
- Minimal, construye ExecutionMetrics

#### **mode_registry.py** (34 líneas)
- ECO: gemini-2.5-flash-lite, $0.05 estimated
- RACING: gemini-2.5-pro, $0.30 estimated

**Estado:** ✅ Correcto

### Aplicación Principal (app.py - 2169 líneas)

**Funciones de BD (110 líneas):**
- ✅ `init_db()`: Crea tablas, sample data
- ✅ `get_projects()`, `get_project()`, `create_project()`, `update_project()`
- ✅ `get_project_tasks()`, `create_task()`, `get_task()`
- ✅ `get_project_assets()`, `create_asset()`
- ✅ `save_execution_result()`: Almacena output, extract, router_summary

**Funciones auxiliares:**
- ✅ `human_size()`, `format_time_ago()`
- ✅ `safe_json_loads()`
- ✅ `display_decision_preview()`: Muestra decisión del Router (NUEVO - feature previa)

**Vistas Principales:**
1. **home_view()** (líneas 1262-1544)
   - Estado ONBOARDING: "Trabaja mejor con IA, sin caos"
   - Estado WITH_ACTIVITY: "Portable Work Router" (versión austera)
   - Input: text_area 110px (ACTUALIZADO)
   - Caption: "Voy a elegir la mejor forma de resolverlo por ti"
   - **NEW:** display_decision_preview() si user escribe
   - Contexto: expander colapsado
   - Botón: "Generar propuesta" (ACTUALIZADO)
   - Secciones: "Retoma tu trabajo", "Tus proyectos"

2. **project_view()** (líneas 1545-2148)
   - Master-detail: 25% sidebar + 75% main
   - Sidebar:
     - Header con nombre proyecto
     - Input: text_area 110px (ACTUALIZADO)
     - Caption: "Voy a elegir..." (ACTUALIZADO)
     - **NEW:** display_decision_preview() si user escribe
     - Contexto: expander
     - Botón: "Generar propuesta" (ACTUALIZADO)
     - Task list: search + click-to-open
   - Main:
     - Botón "Ejecutar"
     - Flujo ejecución: progress visual → execution_service.execute()
     - **PROBLEMA:** st.error() cuando falla (línea 1729)
     - Resultado: text_area editable (280px)
     - 4 botones: Guardar | Mejorar | Personalizar | Re-ejecutar
     - Micro-flujo "Guardar como activo"
     - Flujo "Mejorar con análisis profundo"
     - Expandibles colapsados: Ficha | Prompt | Trazabilidad | Activos
     - Decision display al final (DESPUÉS de expandibles)

**Estado:** ✅ Funcional, pero UX expone detalles técnicos en puntos críticos

---

## 2. CLASIFICACIÓN POR ESTADO

### ✅ Implementado y Funcional
- **Router core**: DecisionEngine, ExecutionService, providers
- **BD**: Schema, CRUD operations, migrations
- **Flujo básico**: Crear proyecto → crear tarea → ejecutar → guardar resultado
- **UX HOME**: Dos estados, captura rápida, lista de proyectos
- **UX PROJECT**: Master-detail, sidebar intuitivo
- **Decision previa**: Implementado (muestra decisión antes de ejecutar)
- **Mejorar**: Flujo completo, RACING mode forzado
- **Guardar como activo**: Micro-flujo, panel inline
- **Trazabilidad**: Expandible con detalles técnicos

### ⚠️ Implementado pero Incompleto
- **MockRacingProvider**: Existe pero nunca se usa (ExecutionService no lo registra)
- **score_model()**: Función vieja (línea 362), NO se usa actualmente
- **Error handling UX**: Manejo correcto en lógica, pero UI expone errores técnicos como st.error()
- **Modo demo**: NO existe. Cuando Gemini no está disponible, devuelve ExecutionError (no propuesta simulada)
- **copy/tone**: Mezcla técnico ("proveedor", "modelo") con usuario ("Voy a elegir")

### 📋 Esbozado / Provisional
- **Backend directory**: Existe pero no se usa (pwr_router_v1_full_fixed/)
- **validate_setup.py**, **run_acceptance_tests.py**: Existen pero no integrados en flujo
- **Detalles técnicos colapsados**: Correctos pero no están bien separados de "experiencia principal"

### ❌ No Implementado
- **Settingss/Configuración**: No hay UI para conectar Gemini. Solo .env.example
- **Fallback elegante**: No hay "modo demo" cuando falta provider
- **Debug mode**: No hay panel separado para tripas técnicas
- **API authentication**: No hay OAuth, solo API key env var
- **File uploads en tasks**: BD soporta, pero upload UI puede estar incompleto
- **Sharing**: No hay features de colaboración/sharing
- **Historial de ejecuciones**: No hay timeline/historial
- **Export/Backup**: No hay opciones de export de datos

---

## 3. NÚCLEO OPERATIVO REAL

### ¿Qué tiene valor de verdad HOY?

**El Router decision es real y útil:**
- ✅ DecisionEngine analiza correctamente complejidad
- ✅ Elige ECO o RACING basado en señales válidas
- ✅ Reasoning path explica la decisión
- ✅ La decisión previa es VISIBLE antes de ejecutar (feature nuevo)

**La ejecución funciona cuando hay Gemini:**
- ✅ Si API key está configurada: ejecuta real, devuelve resultado real
- ✅ Captura de errores explícita y clasificada
- ✅ Métricas reales (latencia, coste estimado)

**La persistencia es sólida:**
- ✅ Proyectos, tareas, activos se guardan
- ✅ Resultados se almacenan
- ✅ Trazabilidad completa

**La UX de captura y organización funciona:**
- ✅ Crear proyecto rápido
- ✅ Capturar tareas con contexto
- ✅ Guardar resultados como activos reutilizables

### ¿Qué es promesa (parece funcionar pero requiere setup)?

**Ejecución real:**
- Parece funcionar si Gemini está conectado
- Sin GEMINI_API_KEY → ExecutionError técnico (no fallback elegante)
- Usuario ve "Provider not available" en UI principal (rompe confianza)

**Modo demo:**
- NO existe. Cuando falla Gemini, devuelve error
- No hay "propuesta simulada útil" basada en análisis del Router
- NO hay forma de aprender qué haría el sistema sin credenciales reales

---

## 4. HUECOS Y DEUDA TÉCNICA

### Problemas Críticos (Product Risk)

**1. Error handling en UX (Línea 1729: st.error)**
```python
if result.status == "error":
    st.error(f"Error: {result.error.message}")  # ❌ EXPONE TRIPAS
```
- Cuando Gemini falla → usuario ve "Provider 'gemini' no disponible"
- Es error técnico, no mensaje para usuario
- **Impacto**: Rompe sensación de producto inteligente
- **Solución**: Detectar error de provider, mostrar estado "Modo demo" con propuesta previa

**2. No existe modo demo/fallback**
- Cuando no hay provider → ExecutionError
- No hay "propuesta simulada" que enseña inteligencia del Router
- Usuario no ve análisis + estrategia + prompt
- **Impacto**: Si usuario no configura API key, PWR parece roto
- **Solución**: A) Crear modo demo explícito, o B) Bloqueo elegante + CTA hacia Settings

**3. Detalles técnicos compiten con propuesta central**
- Línea 2095: "Trazabilidad" expandible (correcto)
- Línea 2121-2147: Decision display al final (después de todo)
- Pero st.error() y reasoning_path técnico aparecen en medio del flujo
- **Impacto**: Usuario ve "provider", "modelo", "API key" en UI principal
- **Solución**: Mover trazabilidad a panel colapsado. Decision previa arriba (ya hecho con feature nuevo).

**4. Reasoning path del Router es muy técnico**
- "Decisión automática: modo RACING. Complejidad estimada: 0.65. Señales detectadas: complejidad técnica, razonamiento estratégico. Criterio: priorizar precisión y profundidad."
- No es para usuario, es para auditor técnico
- **Impacto**: display_decision_preview() extrae primera línea, pero puede ser confusa
- **Solución**: Traducir reasoning_path a lenguaje usuario en decision_engine.py

### Problemas Técnicos (Code Debt)

**1. MockRacingProvider nunca se registra**
- Existe código pero no se usa
- ExecutionService solo registra MockEcoProvider
- **Impact**: Código muerto
- **Solución**: Limpiar o documentar por qué existe

**2. score_model() nunca se usa**
- Función antigua (línea 362) que calculaba modelo sugerido
- Ahora DecisionEngine hace eso
- **Impact**: Código confuso, mantenimiento innecesario
- **Solución**: Eliminar

**3. Separación de concerns confusa**
- app.py maneja BD + UI + lógica de sesión (2169 líneas)
- router/ está separado pero bien
- Pero app.py es monolítica
- **Impact**: Difícil de mantener, navegar
- **Solución**: NO es crítico ahora, pero considerar refactor a futuro

**4. No hay validación de entrada en TaskInput**
- task_type no valida contra TIPOS_TAREA
- Contexto puede ser muy largo sin límite
- **Impact**: Bajo. Router es robusto ante cualquier input.

### Deuda Visual/UX

**1. Error display en rojo (st.error)**
- Línea 1729, 1881
- Visualmente alarmante
- Para errores de configuración, es excesivo
- **Solución**: Usar st.warning() o custom container para fallbacks

**2. Trazabilidad al final en colapsable**
- Línea 2095: "🔍 Trazabilidad"
- Si usuario ejecuta y falla, tiene que abrir expandible para ver error
- **Solución**: Mostrar estado de ejecución más prominentemente

**3. Decision display después de expandibles**
- Línea 2121-2147: Decision display al final
- Debería estar arriba como "propuesta previa"
- (NOTA: Feature nuevo `display_decision_preview()` hace esto en captura, pero no en ejecución)

---

## 5. QUÉ DEBERÍAMOS ABORDAR NEXT

### Bloqueador Crítico Actual

**El estado cuando no hay Gemini es roto:**
1. User escribe tarea
2. Decision previa ✅ se muestra (feature nuevo)
3. User pulsa "Generar propuesta"
4. Tarea se crea ✅
5. User abre resultado → Ejecutar
6. ❌ ExecutionError técnico: "Provider 'gemini' no disponible"
7. User rompe confianza, parece producto incompleto

### Prioridad 1: Fallback Strategy (A)

**Problema de comportamiento, no solo presentación.**

**Opciones:**
- **A1 (Recomendado):** Modo demo explícito
  ```
  ✨ Propuesta previa
  Modo demo activo · La ejecución real requiere conectar un motor

  🧠 Qué he entendido
  Quieres un resumen breve...

  🎯 Cómo lo resolvería
  Lo abordaría de forma rápida...

  💬 Prompt sugerido
  Resume el documento en 3 ideas clave...

  Para generar el resultado real:
  [ Activar ejecución real ]
  Configúralo en Settings
  ```
  - Preserva inteligencia visible
  - Educativo (ve el análisis)
  - No parece roto
  - Permite demo funcional

- **A2:** Bloqueo elegante
  ```
  🔐 Ejecución requiere configuración
  Para usar resultados reales, conecta Gemini
  [ Ir a Settings ]
  ```
  - Claro pero menos valioso
  - Usuario no ve análisis

**Recomendación:** A1 (Modo demo). Más fértil para builder, iteración, y mantiene narrativa inteligencia.

**Cambios requeridos:**
- Detectar si Gemini está disponible (ya lo hace ExecutionService)
- Si no: llamar a una nueva función `generate_demo_proposal()`
- `generate_demo_proposal()` debe:
  - Llamar DecisionEngine.decide()
  - Construir propuesta basada en análisis (sin ejecutar)
  - Mostrar qué-entendí, cómo-lo-resolvería, prompt, salida-esperada
  - Marcar como "Modo simulación"

### Prioridad 2: UI/UX Restructuring (B)

**Una vez A está cerrado, reestructurar visibilidad:**

- Mover st.error() a contenedor inteligente
- Si es error de provider → mostrar "Modo demo" (de A)
- Si es error de ejecución → mostrar warning, no error
- Trazabilidad → siempre colapsada
- Decision previa → prominente (ya está parcialmente con feature nuevo)
- Detalles técnicos → expander "Debug" o "Detalles técnicos"

**Cambios en app.py:**
- Línea 1729: Reemplazar st.error() con lógica de demo
- Línea 2095-2108: Trazabilidad permanece colapsada
- Línea 2121-2147: Decision display es correcto, pero refinar copy

### Prioridad 3: Copy/Tone Polish (C)

**Menos urgente, pero importante:**

- Reasoning path del Router: Traducir a usuario
- Display decision: Menos técnico
- Cambiar "Modo ECO" → "Rápido y preciso"
- Cambiar "Modelo" → quitar si es posible, o resumir

---

## 6. CAPA ESTRATÉGICA: MODEL RADAR (Observatorio de LLMs)

### Visión
Más allá del Router v1 (que hoy decide eco/racing estático), PWR tendrá un **observatorio vivo** que:
- Monitorea cambios en proveedores, modelos, pricing, contexto, capacidades
- Mantiene catálogo dinámico (no hardcoded en mode_registry.py)
- Alimenta decisiones futuras del Router
- Sirve versión pública `/radar` en web de PWR
- Informa sobre estado, cambios, discontinuaciones

### Arquitectura Conceptual Futura
```
Model Catalog (BD)
├── Providers (Gemini, Claude, etc)
├── Models (flash-lite, pro, opus, etc)
│   ├── pricing (input/output tokens)
│   ├── context_window
│   ├── capabilities (vision, reasoning, etc)
│   ├── status (active, deprecated, limited)
│   └── updated_at
├── Historical data (pricing changes, capacity)
└── Observer/fetcher (API que actualiza catálogo)

DecisionEngine v2
├── Usa catálogo vivo (no mode_registry hardcoded)
├── Toma decisiones basadas en datos actuales
└── Expone reasoning que cita catálogo

Public API: /radar
└── Datos públicos del observatorio
```

### Impacto en Trabajo Inmediato (Fallback/Demo A)

**¿Interfiere el fallback con Model Radar?**
- ✅ NO interfiere directamente
- ✅ El fallback (modo demo) ocurre ANTES del Router
- ✅ DecisionEngine sigue siendo el mismo

**¿Qué deberíamos preparar ya?**

1. **Domain model para Model Radar** (pequeño)
   - NO implementar BD ni Observer
   - Pero sí: crear `router/model_catalog.py` con interfaz futura
   - Esto permite DecisionEngine v2 usar catálogo vivo sin reescribir todo

   Ejemplo de estructura a preparar:
   ```python
   # router/model_catalog.py (SCAFFOLD FUTURO)
   class Model:
       name: str
       provider: str
       pricing_input: float
       pricing_output: float
       context_window: int
       status: str  # active, deprecated, limited

   class ModelCatalog:
       """Interface para acceso a modelo vivo.
       Hoy: lee de mode_registry (estático)
       Mañana: lee de BD + Observer
       """
       def get_model(self, name: str) -> Model: ...
       def list_models(self, provider: str) -> List[Model]: ...
   ```

   Luego:
   ```python
   # DecisionEngine hoy
   config = get_mode_config(mode)  # mode_registry hardcoded

   # DecisionEngine futuro (preparado ya)
   catalog = ModelCatalog()
   model = catalog.get_model(mode)  # Puede venir de BD o mode_registry
   ```

2. **Evitar hardcoding de decisiones**
   - Actual: mode_registry.py define directamente eco → flash-lite, racing → pro
   - Futuro: eso vendrá de BD
   - **Recomendación**: Ya que refactorizamos para fallback, envolvemos mode_registry en interfaz
   - Así después insertamos catálogo BD sin tocar DecisionEngine

3. **Tabla en BD para modelo_config (futuro)**
   - NO crear ahora, pero reservar schema
   - Cuando Model Radar esté listo, agregar tabla sin romper nada
   - **Preparación**: En `init_db()`, comentar future schema:
     ```python
     # FUTURO: Model Radar
     # CREATE TABLE IF NOT EXISTS model_catalog (
     #     id INTEGER PRIMARY KEY,
     #     provider TEXT,
     #     model_name TEXT,
     #     pricing_input REAL,
     #     pricing_output REAL,
     #     context_window INTEGER,
     #     status TEXT,
     #     updated_at TEXT
     # )
     ```

**¿Hay algo que debamos evitar ahora?**

❌ **NO hacer:**
- ❌ Agregar DB queries a DecisionEngine (seguirá siendo stateless)
- ❌ Cambiar signatures de ExecutionService (necesitamos mantener compat)
- ❌ Hardcodear más lógica de decisión en app.py
- ❌ Crear tabla model_catalog sin observador (tabla huérfana)

✅ **SÍ hacer:**
- ✅ Wrappear mode_registry en interfaz (ModelCatalog)
- ✅ Dejar DecisionEngine agnóstico a fuente de datos de modelos
- ✅ Documentar dónde va a vivir info de modelos futuro
- ✅ Mantener ExecutionService como orquestador (sin cambios)

**Impacto en Plan A (Fallback):**
- El fallback (modo demo) NO genera propuesta real
- El fallback genera propuesta simulada (análisis + estrategia + prompt)
- Para eso: DecisionEngine sigue igual, solo agregamos UI
- **Conclusión**: Plan A es completamente orthogonal a Model Radar
- Model Radar entraría después, alimentaría DecisionEngine sin cambiar API pública

### Próximas iteraciones (FUTURO, después de A+B+C)
```
Iteración D: Model Catalog schema + Observer skeleton
Iteración E: Conectar DecisionEngine a catálogo vivo
Iteración F: Public /radar API
Iteración G: Web de PWR con historial de cambios
```

---

## STATUS TECH

### Objetivo de esta revisión
Entender estado real del código, qué funciona vs. qué es promesa, qué riesgos tiene la experiencia.

### Lo ya construido de verdad
✅ **Router core** (decision, execution, providers, error handling)
✅ **BD persistente** (projects, tasks, assets, CRUD operations)
✅ **Flujo de captura** (quick input → decision previa → create task)
✅ **Flujo de ejecución** (select task → execute → save result)
✅ **UX básica** (home con dos estados, sidebar intuitivo, trazabilidad)
✅ **Decision previa** (muestra decisión ANTES de ejecutar - feature nuevo)
✅ **Mejorar flujo** (RACING mode forced, comparar resultados)
✅ **Guardar activos** (micro-flujo, reutilización)

### Lo incompleto o frágil
⚠️ **Fallback cuando no hay provider** → ExecutionError técnico, no modo demo
⚠️ **Error handling UX** → st.error() expone tripas en UI principal
⚠️ **Tone inconsistente** → Router reasoning es técnico, UI es usuario
⚠️ **Configuration** → No hay UI para Gemini setup, solo .env.example
⚠️ **MockRacingProvider** → Existe pero nunca se registra (código muerto)
⚠️ **score_model()** → Función vieja no usada

### Mayor riesgo actual
**Cuando Gemini no está disponible, el usuario ve error técnico en UI central.**

Esto rompe la narrativa de "sistema inteligente". La solución es modo demo explícito (propuesta previa útil sin ejecución real).

### Siguiente bloque recomendado
**A) Fallback strategy** (define comportamiento cuando no hay provider)
   → Decide: modo demo vs. bloqueo elegante
   → Implementar: `generate_demo_proposal()` que devuelve qué-entendí, cómo-lo-resuelvo, prompt

**B) UI restructuring** (esconde detalles técnicos, deja propuesta central limpia)
   → Mover error handling a contexto inteligente
   → Trazabilidad colapsada siempre
   → Decision display refinado

**C) Tone refinement** (Router reasoning → lenguaje usuario)
   → decision_engine genera copy más natural
   → Eliminar tecnicismos de UI principal

### Decisión que necesita Albert
1. **Fallback mode:** ¿Modo demo explícito (A1) o bloqueo elegante (A2)?
   - A1 recomendado: Preserva inteligencia visible, educativo, no parece roto
   - A2: Claro pero menos valioso, menos aprendizaje del usuario

2. **Scope A+B+C o solo A?**
   - A es bloqueador crítico (comportamiento roto)
   - B es importante (protege propuesta central)
   - C es pulido (mejora tone)
   - Recomendación: Hacer A completamente, luego B, luego C (orden de dependencias)

3. **Settings/Configuration UI:**
   - ¿Incluir panel de Gemini setup? (fuera de A, pero relacionado)
   - O mantener .env.example solo por ahora?

---

## Resumen Ejecutivo

**PWR tiene un **router inteligente real** que funciona cuando Gemini está disponible. El núcleo es sólido.**

**El problema no es arquitectura, es experiencia:** cuando falta Gemini, el usuario ve error técnico en lugar de una propuesta previa útil. Eso hace que PWR parezca roto, no incompleto.

**El siguiente paso:** Modo demo que muestra análisis + estrategia + prompt sin ejecución real. Eso mantiene la narrativa inteligencia incluso sin credenciales.

**Después:** Reesconder detalles técnicos y refinar tone para que se sienta copiloto, no sistema.

**No es refactoring, es comportamiento + contención de ruido técnico.**

---

## STATUS TECH FINAL

### Estado Actual del Proyecto

**Núcleo operativo:**
- Router v1 (decisión eco/racing estático) = funcional
- Decision previa (visible antes de ejecutar) = nuevo + funcional
- Fallback cuando falta provider = ROTO (error técnico en UI)
- BD persistente = sólida
- UX captura/organización = buena
- UX ejecución/resultados = funcional pero expone detalles técnicos

**Línea estratégica prevista (no implementada aún):**
- Model Radar (observatorio vivo de LLMs) = requiere D, E, F, G futuros
- Impacto en A (fallback): CERO directo, pero conviene preparar interfaz
- Riesgo de encorsetar después: BAJO si wrapeamos mode_registry ahora

### Bloque Inmediato A (Fallback / Modo Demo)

**Qué resuelve:**
- Comportamiento cuando no hay Gemini
- Decision previa sigue visible
- Genera propuesta simulada (qué-entendí, cómo-lo-resuelvo, prompt)
- Marca explícitamente como modo demo
- CTA contextual a Settings (no error técnico)

**Cambios requeridos:**
- Detectar si Gemini disponible (ya lo hace ExecutionService)
- Nueva función: `generate_demo_proposal(decision, task_input)`
- Cambiar lógica ejecución: si error de provider → usar demo
- Cambiar UI: st.error() → contenedor "Modo demo"

**Compatibilidad Model Radar:**
- ✅ Completamente ortogonal
- ✅ DecisionEngine no cambia
- ✅ ExecutionService no cambia
- ⚠️ Pequeño setup: Wrappear mode_registry en ModelCatalog interface (preparar scaffold)
- ⚠️ Documentar: comentar future schema model_catalog en init_db()

**Riesgo actual:**
- Sin fallback: usuario ve error técnico → desconfianza
- Con fallback A: usuario ve propuesta simulada → "Ah, es inteligente pero requiere setup"

### Blockers para Model Radar Futuro (si no preparamos ahora)

| Riesgo | Si no preparamos ahora | Si preparamos en A |
|--------|------------------------|-------------------|
| **Decision hardcoded** | Habrá que refactorizar DecisionEngine v2 | ModelCatalog interface hoy, pluggable mañana |
| **mode_registry.py es fuente única** | Costoso migrar a DB + Observer | Wrapped en interfaz, BD se inserta limpiamente |
| **Schema BD fijo** | Cambios rompen existentes | Reserved schema documented, evolución smooth |
| **ExecutionService apunta a modo_registry** | Refactor necesario | Apunta a ModelCatalog, agnóstico fuente |

**Preparación recomendada en A:**
1. Crear `router/model_catalog.py` (interfaz scaffold)
2. Wrappear `mode_registry` en ModelCatalog
3. Comentar future table schema en init_db()
4. Documentar: "aquí va observer futuro"
5. NO crear BD/tablas, NO implementar observer

**Esfuerzo extra en A:** ~1 hora
**Beneficio:** Model Radar se integra sin refactor después

### Decisiones Pendientes (para Albert)

1. **Fallback mode:** ¿Modo demo explícito (recomendado) o bloqueo elegante?
2. **Orden de trabajo:** ¿A → B → C?
3. **Settings UI:** ¿Incluir panel Gemini setup o solo .env.example?
4. **ModelCatalog prep:** ¿Preparo scaffold en A o lo dejamos para D?

### Próximos bloques después de A

**B - UI/UX Restructuring**
- Trazabilidad colapsada siempre
- Decision display refinado
- Error handling inteligente
- Detalles técnicos → expandible debug

**C - Tone Refinement**
- DecisionEngine → reasoning en lenguaje usuario
- Router explanation menos técnico
- Copy consistente copiloto vs. sistema

**D+ - Model Radar**
- Iteraciones D, E, F, G (futuros)
- ModelCatalog implementado
- Observer integrando datos
- Exposición pública /radar

---

**LÍNEA CLARA:** A resuelve comportamiento roto. B+C protegen propuesta. D+ observan LLMs. Ninguno interfiere si preparamos bien ahora.**
