# OPCIÓN 1 MICROPLAN: Onboarding + Persistencia Útil

**Fecha**: 2026-04-17
**Bloque**: F (Onboarding + Product Clarity)
**Filosofía**: Usuario nuevo entiende qué es PWR sin fricción. Guardamos lo que importa.

---

## 1. HOME / ENTRADA AL PRODUCTO

### Estado actual

```
┌──────────────────────────────┐
│ Portable Work Router         │
│ Diseño sobrio · proyectos    │
│ persistentes · Router v1     │
├──────────────────────────────┤
│ (vacío si es nuevo)          │
│ 🔍 Buscar proyecto           │
└──────────────────────────────┘
```

**Problema**: Usuario ve poco. No sabe qué PWR hace.

### Entrada mejorada

```
Home (Usuario NUEVO - sin proyectos)
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  🚀 Portable Work Router                                │
│                                                          │
│  "Elige el modelo correcto para cada tarea             │
│   sin configurar nada. PWR decide automáticamente."    │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │ ✨ Crear primer proyecto                      │  │
│  │    (large, blue, prominent)                    │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ▾ O explora primero:                                 │
│  ├─ Ver modelos disponibles → Radar                   │
│  └─ Documentación rápida → Docs link                 │
│                                                          │
└──────────────────────────────────────────────────────────┘

Home (Usuario CON proyectos)
┌──────────────────────────────────────────────────────────┐
│ 🏠 Home                                                 │
├──────────────────────────────────────────────────────────┤
│ Proyectos:                                             │
│ • Proyecto 1    (2 tareas)                             │
│ • Proyecto 2    (5 tareas)                             │
│                                                          │
│ Últimas tareas resueltas:                              │
│ └─ [Tarea título] (eco, $0.05, 2 min ago)            │
│                                                          │
│ [Crear nuevo proyecto]                                 │
└──────────────────────────────────────────────────────────┘
```

---

## 2. PRIMER CTA CLARO

### Cambio

```
ANTES: Home vacío esperando que usuario "haga algo"
DESPUÉS: Botón grande "Crear primer proyecto"
```

### Implementación

**Ubicación**: Home prominent (grande, azul, centro)

**Texto**: `✨ Crear primer proyecto`
**Tamaño**: Large
**Acción**:
```python
# En home_view()
if not user_has_projects:
    st.markdown("---")
    if st.button("✨ Crear primer proyecto", use_container_width=True, key="cta_new_project"):
        st.session_state["show_create_dialog"] = True
        st.rerun()
```

**Diálogo de creación** (simple):
```
Modal: "Nuevo Proyecto"
├─ Nombre (input)
├─ Descripción (textarea, opcional)
├─ [Crear] [Cancelar]
```

---

## 3. EXPLICACIÓN PWR EN 2–3 LÍNEAS

### Ubicación
- Home para usuario nuevo (prominente, arriba del CTA)
- Proyecto view (en descripción de qué hace Router)
- Radar (meta: qué es esto que ves)

### Texto recomendado

```
VERSIÓN 1 (Home):
"Portable Work Router elige automáticamente
 el modelo correcto para cada tarea.
 No configuras nada. PWR decide."

VERSIÓN 2 (más detalles):
"Creas una tarea → Describes qué necesitas →
 PWR elige si usa eco (rápido, barato)
 o racing (potente, caro) → Resultado."

VERSIÓN 3 (meta, técnica):
"PWR es un agente inteligente que
 mapea tareas a modelos de IA.
 Lee tu tarea, entiende complejidad, elige modelo."
```

**Decisión de Texto**:
- Home nuevo usuario: Versión 1
- Dentro de proyecto: Versión 2
- Radar/About: Versión 3

**Implementación**:
```python
# home_view(), arriba del CTA
if not user_has_projects:
    st.markdown("""
    ### 🚀 Portable Work Router

    **PWR elige automáticamente el modelo correcto para cada tarea.**

    Describes qué necesitas → PWR analiza → Elige eco (rápido, barato)
    o racing (potente, caro) → Resultado.

    No hay configuración. PWR decide.
    """)
```

---

## 4. CÓMO CONTEXTUALIZAR RADAR DENTRO DEL PRODUCTO

### Cambio de framing

```
ANTES: "📡 Radar" (botón enigmático en sidebar)
DESPUÉS: Contextualizado según dónde esté usuario
```

### En Home (usuario nuevo)

```
Home
├─ Encabezado: PWR explicado
├─ CTA: "Crear proyecto"
├─ Secondary option:
│  "¿Qué modelos tiene PWR?"
│  └─ Link → Radar
└─ "¿Cómo funciona?" → Docs
```

### En Sidebar (siempre)

```
Sidebar:
├─ [📡 Modelos disponibles]  ← cambiar label
│  (era "Radar", ahora es descriptivo)
├─ [🏠 Home]
└─ Proyectos...
```

### En Radar mismo

```
Radar View
├─ Encabezado:
│  "📡 Catálogo vivo de PWR"
│
├─ Explicación (2 líneas):
│  "Ves aquí qué modelos PWR puede usar para resolver tareas.
│   Este es el catálogo en tiempo real que influye en las decisiones del Router."
│
├─ ⚠️ Nota importante (footer):
│  "Esto NO es un observatorio histórico.
│   NO ves aquí cuándo se usó cada modelo.
│   NO hay métricas de uso. Solo configuración."
│
└─ [...catálogo...]
```

### Contexto por vista

| Contexto | Label | Narrativa |
|----------|-------|-----------|
| Home nuevo | "¿Qué modelos?" | Onboarding: qué puede resolver PWR |
| Sidebar | "Modelos disponibles" | Meta: catálogo vivo que PWR usa |
| Radar page | "Catálogo vivo" | Technical: vés qué tiene PWR |
| Futuro público | "Capacidades de PWR" | Marketing: qué puede hacer |

---

## 5. PERSISTENCIA MÍNIMA ÚTIL

### Qué DEBE persistir (obligatorio)

| Entidad | Campos | Por qué |
|---------|--------|--------|
| **projects** | name, slug, description, objective, base_context, instructions | Historial usuario, reusabilidad |
| **tasks** | title, description, type, context, status | Qué ha hecho usuario |
| **llm_output** | output completo | Resultado, es el deliverable |
| **router_summary** | decision summary | Explicación de qué PWR eligió |
| **assets** | processed results, outputs | Deliverables procesados, reutilizables |
| **model_catalog** | providers, models, capabilities, costs | Configuración sistema (viva) |

### Qué está pero NO usar aún (esperar E2+)

| Entidad | Por qué NO | Cuándo SÍ |
|---------|-----------|----------|
| router_metrics_json | Aún no hay observatorio | E2: dashboard de uso |
| executions_history | Aún no hay reportes | E2: tabla de ejecuciones |

### Qué NO persistir

| Cosa | Por qué |
|------|--------|
| Logging granular (scores, umbrales) | Overkill, DecisionEngine es caja negra |
| Métricas agregadas | Nadie las ve sin dashboard |
| User preferences | Aún no multiuser |
| API keys | Peligroso, mejor env vars |

### Implementación: Qué cambios en schema

```python
# En init_db(), CONFIRMAR que estos campos existen y funcionan:

# ✅ projects: name, slug, description, objective, base_context, base_instructions
# ✅ tasks: title, description, type, context, status, suggested_model, router_summary
# ✅ tasks: llm_output, useful_extract (ya están)
# ✅ assets: project_id, task_id, title, content (para deliverables)
# ✅ model_catalog: provider, model_name, mode, estimated_cost_per_run, capabilities_json, status, is_internal

# ⚠️ NO agregar:
#   - user analytics tables
#   - metrics aggregations
#   - preferences tables
#   - logs tables
```

### Documentación: Qué guardamos y por qué

```python
# Archivo: PERSISTENCE_POLICY.md (documentar)

Guardamos:
- Proyectos (historial usuario)
- Tareas (qué hizo)
- Outputs (deliverables)
- Decisiones (explicación)
- Assets (reutilizables)
- Catálogo (configuración viva)

No guardamos aún:
- Observatorio (esperar E2)
- Métricas (esperar E2)
- User prefs (esperar multiuser)
- Logging técnico (caja negra intencional)

Mensake hacia usuario:
"PWR guarda tu trabajo. Histórico y análisis vienen después."
```

---

## 6. SCOPE / FUERA DE SCOPE

### ✅ DENTRO DE SCOPE F (Opción 1)

```
Implementación:
├─ Home mejorada (nuevo vs existente)
├─ CTA "Crear primer proyecto"
├─ Explicación PWR (2–3 líneas)
├─ Renombrar/contextualizar Radar
├─ Documentar persistencia
└─ Limpiar UI innecesaria

Cambios de UX:
├─ Mensajes más claros
├─ Navegación simplificada
├─ Radar menos misterioso
└─ Home informativa

Sin código nuevo:
├─ Mantener lógica existente
├─ Sin nuevas features
├─ Sin nuevos endpoints
```

### ❌ FUERA DE SCOPE F

```
No tocar:
├─ Router lógica (A, B, D, E0 cerrados)
├─ Executions histórico (E2)
├─ Observatorio (E2)
├─ Multiuser (E4)
├─ API real (E3)
├─ Auth avanzada
└─ Mobile responsiveness (futura)

No agregar:
├─ Nuevas tablas BD
├─ Analytics/métricas
├─ Preferences UI
├─ Logging granular
└─ Features escondidas
```

---

## PREPARACIÓN DE OPCIÓN 2

### Framing: "Radar Público"

**Qué es**: Catálogo de PWR accesible sin login.
**Propósito**: "Mira qué puede hacer PWR" (marketing light).
**Ubicación**: `/radar` (URL pública) + landing mínima.

### Arquitectura (sin implementar aún)

```
HOJA DE RUTA OPCIÓN 2:
├─ FASE 1: Decisión arquitectura (NOW)
│  ├─ ¿Streamlit page público? (genera /radar vía Streamlit)
│  ├─ ¿Landing estática? (HTML simple)
│  └─ ¿Combinado? (landing + link a /radar)
│
├─ FASE 2: Diseño (semana 1-2)
│  ├─ Landing: "Qué es PWR"
│  ├─ Catálogo: modelo, capacidades, costo
│  └─ CTA: "Crear cuenta" / "Ver más"
│
└─ FASE 3: Implementación (semana 2-3)
   ├─ Deploy /radar público (sin login)
   ├─ Testing de consistencia
   └─ Link desde landing → /radar
```

### Decisiones pendientes (espera Opción 1)

| Decisión | Opciones |
|----------|----------|
| Transporte | Streamlit page vs Landing estática vs Combinado |
| Autenticación | Sin login totalmente vs "Sign up" CTA |
| Alcance | Solo catálogo vs "Ven y prueba" |
| Hosting | Mismo site que PWR vs Subdomain |

### NO HACER AÚN

```
❌ No implementar código
❌ No crear landing
❌ No diseñar /radar público
❌ No decidir hosting

✅ SÍ en paralelo:
  - Documentar decisiones pendientes
  - Sketches UI ligeros
  - Propuesta de textos
```

---

## ARCHIVOS A TOCAR (OPCIÓN 1)

```
Modificar:
├─ app.py
│  ├─ home_view() mejorada (nuevo vs existente)
│  ├─ Agregar CTA "Crear proyecto"
│  ├─ Explicación PWR (2-3 líneas)
│  └─ Mejorar textos sidebar/nav
│
├─ router/model_catalog.py
│  └─ (Sin cambios, solo ya está listo)
│
└─ Documentación (NEW)
   ├─ PERSISTENCE_POLICY.md (qué guardamos)
   └─ ONBOARDING_FLOW.md (cómo entra usuario)

Opcional refactor:
├─ Limpiar CSS innecesario
└─ Revisar textos en UI (coherencia)
```

---

## STATUS TECH F (OPCIÓN 1)

```
╔════════════════════════════════════════════════════════════════════════════╗
║              OPCIÓN 1: Onboarding + Persistencia Useful                    ║
╚════════════════════════════════════════════════════════════════════════════╝

Objetivo actual:
  Microplan disciplinado de Opción 1
  + Framing de Opción 2 (sin implementar)

Hecho:
  ✅ 1. Home/entrada mejorada (nuevo vs existente)
  ✅ 2. CTA claro ("Crear primer proyecto")
  ✅ 3. Explicación PWR (3 versiones por contexto)
  ✅ 4. Radar contextualizado (no misterioso)
  ✅ 5. Persistencia mínima útil (qué guardar, qué no)
  ✅ 6. Scope claro (dentro/fuera)
  ✅ BONUS: Opción 2 framing (sin implementar aún)

En progreso:
  NADA (es microplan, no ejecución)

Bloqueos:
  NINGUNO técnico

Riesgos identificados:
  - Home nuevo usuario: si no queda claro, usuario se pierde
  - Radar label: cambiar "Radar" → "Modelos" ayuda mucho
  - Persistencia: si no documentamos, confusión en E2+

Siguiente paso:
  Autorización → Implementación F

Decisión que necesita Albert:
  1. ¿Apruebas microplan F como está?
  2. ¿Cambios a textos/orden?
  3. ¿Cuándo esperas que inicie F?
  4. ¿Opción 2 framing queda como está (no implementar)?

════════════════════════════════════════════════════════════════════════════

SÍNTESIS:

F mejora entrada al producto. Usuario nuevo:
  Entra → Lee qué es PWR → Ve CTA claro → Crea proyecto O ve Radar
  (vs hoy: entra → ve Home vacío → ¿?)

Persistencia queda clara:
  Guardamos lo que usuario ve y reutiliza.
  Histórico/análisis son E2.

Opción 2 lista para cuando F esté done.

════════════════════════════════════════════════════════════════════════════
```

