# OPCIÓN 1 / F IMPLEMENTATION SUMMARY
## Onboarding + Persistencia Útil

**Fecha**: 2026-04-17
**Bloque**: F (Product Clarity & Onboarding)
**Estado**: ✅ COMPLETADO

---

## 1. RESUMEN EXACTO DE CAMBIOS APLICADOS

### Cambio 1: Home - Títulos y Copy Reescrito

**Archivo**: `app.py` (líneas 1815-1830)

**ANTES**:
```
Título: "Trabaja mejor con IA, sin caos"
Subtítulo: "Captura tareas, el sistema decide cómo ejecutarlas y guarda resultados reutilizables."
Ayuda: "El sistema elegirá el mejor modelo automáticamente"
```

**DESPUÉS**:
```
Título: "🚀 Portable Work Router"
Subtítulo: "Describe una tarea y PWR te ayuda a decidir cómo abordarla,
           qué modo usar y cómo convertir el resultado en algo reutilizable."
Ayuda: "PWR analizará la complejidad y elegirá el modelo más adecuado"
```

**Diferencias clave**:
- ✅ Emphasize "structural work" + reusability (no promises of "sin configurar")
- ✅ Explicit mention of "convertir resultado en algo reutilizable"
- ✅ PWR como decisor, not as "automatic chooser"
- ✅ More honest framing: analiza y elige (no "sin interacción")

---

### Cambio 2: Radar - Narrativa Mejorada (Keep "Radar" word)

**Archivo**: `app.py` (líneas 1683-1692)

**ANTES**:
```
"Live catalog snapshot — Qué modelos y capacidades tiene PWR hoy.

Esto es un catálogo vivo de configuración. NO es observatorio histórico,
NOT benchmarking, NOT health monitor."
```

**DESPUÉS**:
```
"Catálogo vivo de PWR — Qué modelos y modos tiene PWR para ayudarte a
decidir cómo abordar tareas.

Aquí ves la configuración en tiempo real que PWR consulta para elegir
el modelo más adecuado (eco: rápido/barato, racing: potente/caro).

⚠️ Esto NO es observatorio histórico. NO ves cuándo se usó cada modelo.
Solo el catálogo de disponibilidad."
```

**Diferencias clave**:
- ✅ Keep word "Radar" (no change to "Modelos disponibles")
- ✅ Explain PURPOSE: "ayudarte a decidir cómo abordar tareas"
- ✅ Link to Router decision: "PWR consulta esto para elegir modelo"
- ✅ Clear on what it IS NOT: "NO es observatorio"

---

### Cambio 3: Persistencia Documentada

**Archivo**: `PERSISTENCE_POLICY.md` (NEW FILE)

**Contenido**:
- Qué guardamos obligatoriamente (projects, tasks, outputs, router_summary, assets, model_catalog)
- Qué guardamos pero no usamos aún (router_metrics_json, executions_history)
- Qué no guardamos (logging, preferences, secrets)
- Por qué cada decisión
- Impacto si NO guardáramos
- Visibilidad al usuario
- Timeline (ahora vs E2+ vs E3+)

**Propósito**: Claridad total sobre persistencia. Usuario (y equipo) sabe qué datos persisten y por qué.

---

## 2. CAPTURAS / DESCRIPCIÓN DE HOME Y NAVEGACIÓN

### Home - Usuario NUEVO (sin proyectos)

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│  🚀 Portable Work Router                                                 │
│                                                                            │
│  Describe una tarea y PWR te ayuda a decidir cómo abordarla,            │
│  qué modo usar y cómo convertir el resultado en algo reutilizable.      │
│                                                                            │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  Capturar tarea                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │ Ej: resume este documento • escribe un email • analiza...       │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                                                            │
│  PWR analizará la complejidad y elegirá el modelo más adecuado          │
│                                                                            │
│  [📝 Probar con un ejemplo] [Capturar]                                   │
│                                                                            │
├────────────────────────────────────────────────────────────────────────────┤
│  Cómo funciona                                                            │
│                                                                            │
│  1. Analizamos 🔍          2. Elegimos 🎯         3. Obtienes ✨         │
│  Tu tarea entra             El mejor modelo        Resultado editable     │
│  al sistema                 para cada tipo         y reutilizable         │
│                                                                            │
├────────────────────────────────────────────────────────────────────────────┤
│  Proyectos                                                               │
│  No tienes proyectos todavía. Tu primera tarea creará uno automáticamente│
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Home - Usuario CON PROYECTOS

```
┌────────────────────────────────────────────────────────────────────────────┐
│ 🏠 Home                                                                   │
│                                                                            │
│ Portable Work Router                                                      │
│ Retoma tu trabajo • captura tareas • usa el mejor modelo                 │
│                                                                            │
│ Trabajando en: Mi primer proyecto                                         │
│                                                                            │
│ ¿Qué necesitas hacer ahora?                                              │
│ ┌──────────────────────────────────────────────────────────────────┐    │
│ │ Ej: resume documento, escribe email, analiza gráfico...         │    │
│ │ (textarea, 100px)                                                │    │
│ └──────────────────────────────────────────────────────────────────┘    │
│                                                                            │
│ [📝 Ejemplo] [Capturar]                                                   │
│                                                                            │
├────────────────────────────────────────────────────────────────────────────┤
│ Últimas tareas:                                                           │
│ • Resume del documento (eco, $0.05, 2 min ago)                          │
│ • Email profesional (racing, $0.30, 1h ago)                             │
│                                                                            │
│ [+ Nuevo proyecto]                                                        │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Navegación Sidebar

```
┌────────────────────────┐
│ Portable Work Router   │
├────────────────────────┤
│ [📡 Radar] [🏠 Home]  │
├────────────────────────┤
│ 🔍 Buscar proyecto     │
│ • Mi primer proyecto   │
│ • Proyecto 2           │
│                        │
│ [+ Nuevo proyecto]     │
├────────────────────────┤
│ "Diseño sobrio ...     │
│  Router v1 integrado"  │
└────────────────────────┘
```

---

## 3. TEXTOS FINALES USADOS

### Home - Onboarding (usuario nuevo)

```
Título:
"🚀 Portable Work Router"

Subtítulo:
"Describe una tarea y PWR te ayuda a decidir cómo abordarla,
 qué modo usar y cómo convertir el resultado en algo reutilizable."

Input placeholder:
"Ej: resume este documento • escribe un email • analiza este texto..."

Ayuda input:
"PWR analizará la complejidad y elegirá el modelo más adecuado"

Cómo funciona:
"1. Analizamos 🔍
  Tu tarea entra al sistema

2. Elegimos 🎯
  El mejor modelo para cada tipo

3. Obtienes ✨
  Resultado editable y reutilizable"

Proyectos (vacío):
"No tienes proyectos todavía. Tu primera tarea creará uno automáticamente."
```

### Radar - Encabezado

```
Título:
"📡 Radar"

Descripción:
"Catálogo vivo de PWR — Qué modelos y modos tiene PWR para ayudarte
 a decidir cómo abordar tareas.

Aquí ves la configuración en tiempo real que PWR consulta para elegir
el modelo más adecuado (eco: rápido/barato, racing: potente/caro).

⚠️ Esto NO es observatorio histórico. NO ves cuándo se usó cada modelo.
Solo el catálogo de disponibilidad."

Toggle:
"🔧 Mostrar modelos internos (debug)"
"Modelos mock/test solo para desarrollo"
```

### Persistencia - Mensaje al usuario

```
En Home:
"PWR guarda tus proyectos, tareas y resultados.
 Aquí siempre verás tu historial de trabajo.
 Estadísticas y análisis vienen después."

En Radar:
"Este es el catálogo de modelos que PWR consulta.
 NO ves aquí cuándo se usó cada uno. Solo la configuración."
```

---

## 4. PERSISTENCIA: QUÉ QUEDA EXPLÍCITAMENTE VISIBLE/DOCUMENTADA

### Visible en UI

**En Home / Proyectos**:
- ✅ Proyectos guardados (nombre, descripción)
- ✅ Tareas guardadas (título, descripción, tipo)
- ✅ Resultados (llm_output, useful_extract)
- ✅ Decisión del Router (router_summary: modo, modelo, costo)

**En Radar**:
- ✅ Catálogo vivo (providers, modelos, capacidades, costos)
- ✅ Configuración en tiempo real
- ❌ NO: histórico de cuándo se usó cada modelo

**En Assets**:
- ✅ Deliverables procesados (guardados, reutilizables)

### Documentado en Código

**Archivo**: `PERSISTENCE_POLICY.md`

```
Secciones:
1. QUÉ GUARDAMOS (OBLIGATORIO)
   - projects, tasks, llm_output, router_summary, assets, model_catalog
   - Por qué cada uno

2. QUÉ GUARDAMOS PERO NO USAMOS AÚN (E2+)
   - router_metrics_json, executions_history
   - Para qué servirán

3. QUÉ NO GUARDAMOS (DELIBERADAMENTE)
   - logging técnico, métricas agregadas, preferences, API keys
   - Por qué no guardar

4. IMPACTO SI NO GUARDÁRAMOS
   - Crítico: projects, tasks, outputs, model_catalog
   - Alto: router_summary, assets

5. VISIBILIDAD AL USUARIO
   - Qué ve el usuario de cada entidad

6. TIMELINE
   - Ahora (F): esto
   - E2+: observatorio, análisis
   - E3+: export, audit, compliance
```

### En código (comments)

**En app.py (home_view)**:
```python
# Persistencia: projects, tasks, outputs guardados
# Usuario ve: historial de trabajo, resultados reutilizables
# NO: estadísticas (esperar E2)
```

**En app.py (radar_view)**:
```python
# Catálogo vivo que PWR consulta
# Usuario ve: modelo, capacidades, costo, modo
# NO ve: histórico de uso (esperar E2)
```

---

## 5. CONFIRMACIÓN: OPCIÓN 2 SOLO EN FRAMING

✅ **CONFIRMADO**: Opción 2 (Radar público) queda **solo en framing**, sin implementación.

**Dónde está el framing de Opción 2**:
- Archivo: `OPTION_1_MICROPLAN.md`
- Sección: "PREPARACIÓN DE OPCIÓN 2"
- Contenido: Decisiones pendientes, arquitectura, NO implementación

**Estado**:
- ✅ Framing documentado
- ❌ Código sin cambios
- ❌ Landing sin crear
- ❌ /radar público sin exponer

**Cuándo se implementa**:
- Después de que F esté validado visualmente
- Probablemente semana siguiente
- Decisiones de arquitectura pendientes (Streamlit vs Landing vs Combinado)

---

## STATUS TECH F

```
╔════════════════════════════════════════════════════════════════════════════╗
║              OPCIÓN 1 / F: IMPLEMENTATION COMPLETE ✅                      ║
╚════════════════════════════════════════════════════════════════════════════╝

Objetivo:     Implementar Onboarding mejorado + Persistencia clara
              (con ajustes: copy más fiel, Radar contextualizado)

Hecho:
  ✅ 1. Copy principal reescrito (énfasis en trabajo estructurado)
  ✅ 2. Home mejorada (nuevo user claramente explicado)
  ✅ 3. Radar contextualizado (mantiene palabra, mejor narrativa)
  ✅ 4. Persistencia documentada (PERSISTENCE_POLICY.md)
  ✅ 5. Textos finales claros y coherentes
  ✅ 6. Opción 2 framing (sin implementar)

En progreso:
  NADA (implementación completa)

Bloqueos:
  NINGUNO

Riesgos:
  - Home nuevo usuario: debe quedar claro (ahora SÍ, más claro que antes)
  - Radar: word "Radar" mantenida, contexto mejorado (risgo bajo)
  - Persistencia: explícitamente documentada (riesgo bajo)

Validación pendiente:
  ✅ Técnica: DONE (código en app.py + docs)
  ⏳ Visual: USER PENDING (cuando pruebe en entorno real)

Archivos modificados:
  ├─ app.py (líneas 1815-1830: copy + radar narrative)
  │
  Archivos creados:
  ├─ PERSISTENCE_POLICY.md (documentación clara de persistencia)
  └─ F_IMPLEMENTATION_SUMMARY.md (este documento)

Siguiente paso:
  1. Validación visual de F en entorno real
  2. Si OK: proceder a Opción 2 (Radar público)
  3. Si ajustes: iterar

Decisión que necesita Albert:
  1. ¿Textos finales OK? (Home, Radar, persistencia)
  2. ¿Cuándo puede validar F visualmente?
  3. ¿Proceder a Opción 2 sin cambios a F?

════════════════════════════════════════════════════════════════════════════

SÍNTESIS:

F mejora entrada al producto. Usuario nuevo:
  Entra → Lee PWR CLARO (no promesas vacías) → Ve CTA → Crea proyecto
  (vs antes: entra → ve "trabaja mejor sin caos" → confundido)

Persistencia CLARA:
  Guardamos: lo que usuario ve y reutiliza (proyectos, tareas, outputs)
  Preparamos: lo que usaremos en E2 (observatorio)
  No guardamos: lo que no importa aún (logging, analytics)

Radar CONTEXTUALIZADO:
  Mantiene palabra "Radar"
  Pero claro: "esto es el catálogo que PWR consulta, NO es observatorio"
  Mejorado: explica PURPOSE y LIMIT

Opción 2 READY:
  Framing documentado en OPTION_1_MICROPLAN.md
  Sin implementación aún
  Decisiones pendientes: transporte, scope, hosting

════════════════════════════════════════════════════════════════════════════
```

