# PRODUCT REVIEW: Post-E1 Analysis
## Qué sigue después de Radar v1

**Fecha**: 2026-04-17
**Contexto**: Bloques A, B, D, E0, E1 cerrados. Sistema funciona. Pregunta: ¿qué construir después?
**Nota**: Esta es una revisión de PRODUCTO, no de ingeniería. Foco en visibilidad, onboarding, persistencia.

---

## 1. ONBOARDING: Qué ve un usuario por primera vez

### Estado actual

```
┌─ Login / Acceso
│
└─ Home View
   ├─ "Portable Work Router"
   ├─ Proyectos vacíos (si es nuevo)
   ├─ "Diseño sobrio · proyectos persistentes · Router v1 integrado"
   └─ Sidebar: project_selector (vacío)
```

**Problema**: Un usuario nuevo ve:
- ❓ ¿Qué es PWR?
- ❓ ¿Qué hago aquí?
- ❓ ¿Dónde está el Router?
- ❓ ¿Qué es Radar?

### Qué debería pasar

#### Escenario 1: Usuario nuevo (sin proyectos)

```
Home (vacío)
├─ Encabezado claro:
│  "PWR: Portable Work Router"
│  "Tu asistente inteligente para resolver tareas con el modelo correcto"
│
├─ Explicación sin fricción (3 líneas):
│  "Creas una tarea → PWR elige el modelo (eco o racing) → Resuelve"
│  "No configuras nada. El Router decide automáticamente."
│
├─ Botón prominente:
│  "Crear primer proyecto" (large, blue)
│
├─ Secondary:
│  "Ver Radar" (catálogo de modelos)
│
└─ Footer:
   "¿Cómo funciona?" (link a docs light)
```

#### Escenario 2: Usuario con 1+ proyectos

```
Home (con actividad)
├─ Proyectos listados (ya funciona)
├─ Últimas tareas (si existen)
├─ Quick access a Radar
└─ (Sin onboarding repetitivo)
```

### Cómo introducir Radar sin ruido

**HOY** (E1):
- Radar es un botón en sidebar
- Muestra catálogo vivo
- Narrativa: "Ves qué modelos tiene PWR hoy"

**PROBLEMA**: Radar se ve como "herramienta avanzada" para usuarios técnicos.
- ❓ ¿Un user normal sabe qué hacer con Radar?
- ❓ ¿Es confuso verlo junto a proyectos?

**SOLUCIÓN LIGERA**:
- Radar vive en sidebar (como está hoy) ✅
- Pero visible solo en contexto: cuando usuario PREGUNTA "¿qué modelos tienes?"
- O: pestaña en Home tipo "Sobre PWR" → ve Radar

**RECOMENDACIÓN para onboarding**:
```
Home (nuevo usuario)
├─ Explicación: 3 líneas (PWR es, cómo funciona, qué hace)
├─ Botón: "Crear proyecto"
├─ Botón secondary: "Ver modelos disponibles" → abre Radar
└─ No es "Radar" (palabra técnica), es "Modelos disponibles"
```

---

## 2. PERSISTENCIA: Qué datos deben persistir de verdad

### Hoy tenemos

```
BD (pwr.db):
├─ projects (nombre, slug, descripción, objetivo, context, instructions)
├─ project_documents (uploads de usuario)
├─ tasks (title, description, type, context, router_summary, llm_output)
├─ assets (resultados guardados)
├─ model_catalog (catálogo vivo)
├─ executions_history (minimalista: task_id, mode, model, provider, latency, cost)
```

### Análisis: Qué TIENE que persistir

| Entidad | ¿Guardar? | Razón | Impacto si NO |
|---------|-----------|-------|---------------|
| **projects** | ✅ SÍ | Base de historial usuario | Usuario pierde todo |
| **tasks** | ✅ SÍ | Historial de lo que hizo | Usuario no ve su trabajo |
| **llm_output** | ✅ SÍ | Resultado es el deliverable | Usuario pierde output |
| **router_summary** | ✅ SÍ | Explicación de decisión | Usuario no entiende qué pasó |
| **router_metrics_json** | ⚠️ CONDICIONAL | ¿Para análisis o visibilidad? | Sin E2 observatorio, es metadato |
| **executions_history** | ⚠️ CONDICIONAL | ¿Para auditoría o métricas? | Sin uso aparente en E1 |
| **model_catalog** | ✅ SÍ | Configuración del sistema | Router no sabe qué modelos existen |
| **project_documents** | ✅ SÍ | Context del usuario | Router pierde contexto |
| **assets** | ✅ SÍ | Deliverables procesados | Usuario no puede reutilizar |

### Qué NO hace falta guardar todavía

| Cosa | Por qué NO | Cuándo SÍ |
|------|-----------|----------|
| Histórico de cambios en model_catalog | No hay versionado | E3+ (observatorio real) |
| Logs de decisión internos (scores, umbrales) | DecisionEngine es caja negra | E2+ (scoring adaptativo) |
| Métricas agregadas por usuario/proyecto | Nadie las ve | E2+ (dashboard) |
| User preferences (tema, idioma, etc) | Aún no hay multiuser | E4+ (multi-tenant) |
| Audit trail completo | Overkill para prototipo | E3+ (compliance) |
| API keys de providers | Peligroso guardar, mejor env vars | E3+ (admin panel) |

### Recomendación de persistencia

**Hoy** (E1):
- ✅ Guardar: projects, tasks, llm_output, router_summary, model_catalog, assets
- ⚠️ Guardar pero no exponer: router_metrics_json (para E2+), executions_history (para E2+)
- ❌ NO guardar: logging granular, métricas agregadas, preferences

**Mensaje**:
> "Guardamos lo que el usuario necesita ver y reutilizar. Métricas y análisis vienen después."

---

## 3. ACCESO AL RADAR: Visibilidad sin sobreprometer

### Pregunta clave

**¿Radar es herramienta o feature de producto?**

### Hoy (E1)

```
Sidebar:
├─ 📡 Radar (botón)
├─ 🏠 Home
└─ Proyectos
```

**Radar vive en sidebar como iguales a Home/Proyectos**
→ Parece que Radar es otra "sección" del producto
→ Pero es solo "catálogo vivo", no es "observatorio"
→ Posible fricción: usuario espera más de lo que Radar hace

### Opciones

#### Opción A: Radar dentro de PWR (sidebar)
```
✅ Ventaja:
  - Visible, accesible
  - Refuerza "PWR sabe qué hace"

❌ Riesgo:
  - Usuario puede pensar "¿por qué no veo mis usos aquí?"
  - Parece incompleto si no hay histórico
```

#### Opción B: Radar en "About PWR" o "Settings"
```
✅ Ventaja:
  - Contextualizado como "meta" (sobre el sistema)
  - Menos confuso: no es una "sección" funcional

❌ Riesgo:
  - Menos visible
  - Usuario puede no descubrirlo
```

#### Opción C: Radar en Home (solo para nuevos usuarios)
```
✅ Ventaja:
  - Onboarding: explica "eso es lo que te puede resolver"

❌ Riesgo:
  - Desaparece cuando usuario ya tiene proyectos
  - Confuso: dónde está Radar después
```

### Recomendación: Parte pública, parte interna

```
PÚBLICO (URL pública, sin login):
  /radar
  └─ Catálogo minimalista: "PWR puede usar estos modelos"
  └─ Propósito: "mira qué tenemos" (marketing light)
  └─ Scope: providers, modelos, capacidades (no internos)

INTERNO (dentro de PWR autenticado):
  📡 Radar en sidebar
  └─ Propósito: "esto es lo que usamos para ti"
  └─ Scope: igual a la versión pública hoy
  └─ Futuro: con /api/radar y estadísticas por usuario
```

### Cómo exponerlo sin sobreprometer

**Texto en Radar**:
```
"Catálogo vivo de PWR

Ves aquí qué modelos y capacidades PWR puede usar hoy.

⚠️ NOTA:
  - Esto es un snapshot del catálogo.
  - NO es un observatorio de tu uso.
  - NO es un monitor de salud.
  - NO tiene scoring o analytics aún.

Después:
  - Verás estadísticas de tus usos
  - Sabrás cuándo PWR elige cada modelo
  - Tendrás insights de decisiones
"
```

---

## 4. RECOMENDACIÓN: Las 3 opciones siguientes razonables

### OPCIÓN 1: Pulir Onboarding + Persistencia
**Scope**: No código nuevo de features. Solo UX cleanup.

```
1. Onboarding para nuevos usuarios
   └─ Explicar PWR en 3 líneas claras
   └─ Botón "Crear proyecto" prominente
   └─ Link a Radar como "Ver modelos disponibles"

2. Revisar qué guardamos
   └─ Confirmar: projects, tasks, outputs, assets son útiles
   └─ Marcar: router_metrics_json, executions_history para E2+

3. Radar: contextualizarlo mejor
   └─ Cambiar narrativa de "Radar" → "Catálogo"
   └─ Footer claro: "NO es observatorio"
```

**Beneficio**: Producto se siente más pulido, menos confuso.
**Tiempo**: 1 semana.
**Riesgo**: Bajo (solo UX, no lógica).

---

### OPCIÓN 2: Exposición Pública (Radar público)
**Scope**: Hacer que Radar sea accesible sin login como "vitrina".

```
1. Endpoint público /radar (sin Flask, vía Streamlit page)
   └─ Catálogo minimalista: providers, modelos, capacidades
   └─ Propósito: "mira qué puede resolver PWR"

2. Landing page mínima
   └─ "Portable Work Router"
   └─ "Usa el modelo correcto para cada tarea"
   └─ "Modelos disponibles:" → link a /radar

3. Integración en home (usuario no logged)
   └─ Opción: "Ver modelos sin login"
```

**Beneficio**: PWR se ve públicamente, gana credibilidad.
**Tiempo**: 2-3 semanas (Streamlit page + landing light).
**Riesgo**: Medio (exposición pública, mantener consistencia).

---

### OPCIÓN 3: Observatorio Ligero (E2 mini)
**Scope**: Visualizar executions_history de forma simple.

```
1. Nueva vista: "Uso" o "Historial"
   └─ Tabla simple: últimas 20 ejecuciones
   └─ Columnas: tarea, modelo usado, costo, latencia
   └─ Filtro: por proyecto, modo

2. Dashboard minimalista
   └─ "Tareas resueltas: 42"
   └─ "Modelo favorito: gemini-2.5-flash-lite"
   └─ "Costo total: $5.43"

3. Conexión con Radar
   └─ "Modelos que usaste" (vs disponibles)
```

**Beneficio**: Usuario ve "qué ha hecho", refuerza valor de PWR.
**Tiempo**: 3-4 semanas (nueva vista + queries).
**Riesgo**: Medio (evitar sobre-prometer "observatorio").

---

## CUÁL HARÍAS AHORA MISMO

### Recomendación: **OPCIÓN 1 + inicio de OPCIÓN 2**

**Razonamiento**:

1. **OPCIÓN 1 (Onboarding + Persistencia)** es **obligatoria**
   - Usuario nuevo actualmente se pierde
   - Decisión sobre persistencia afecta todo
   - Bajo riesgo, alto impacto de producto
   - Hoy mismo

2. **OPCIÓN 2 (Radar público)** es **ventaja de posicionamiento**
   - PWR sale del "prototipo privado" al "producto con visibilidad"
   - Catálogo público es poderoso: "mira qué puedo hacer"
   - Prepara el terreno para usuarios
   - Comenzar en paralelo (no esperar a que termine Opción 1)

3. **OPCIÓN 3 (Observatorio)** es **prematura**
   - Requiere decisiones sobre "qué métricas importan"
   - Mejor hacerla después de feedback real de Opción 1+2
   - E2 puede esperar 2-3 semanas

### Plan concreto

```
AHORA (semana 1):
├─ OPCIÓN 1: Onboarding + Persistencia
│  ├─ Crear vista "Home mejorada" (nuevo usuario vs existente)
│  ├─ Texto claro: qué es PWR, cómo funciona
│  ├─ Radar: renombrar a "Catálogo", contextualizar
│  └─ Documentar: qué guardamos y por qué
│
└─ OPCIÓN 2 (inicio): Arquitectura pública
   ├─ Decidir: ¿Streamlit page public o página estática?
   ├─ Diseñar landing mínima
   └─ Conectar /radar público

SEMANA 2-3:
├─ OPCIÓN 2 (completar): Deploy radar público
│  ├─ Testing en entorno público
│  └─ Validación de consistencia
│
└─ Recopilar feedback

SEMANA 4+:
├─ Decidir: ¿OPCIÓN 3 (Observatorio)?
└─ Basado en feedback real de usuarios
```

---

## STATUS TECH

```
╔════════════════════════════════════════════════════════════════════════════╗
║                   POST-E1: Revisión de Producto                            ║
╚════════════════════════════════════════════════════════════════════════════╝

Objetivo actual:
  Definir siguiente fase de producto (no técnico)
  Analizar: onboarding, persistencia, Radar, recomendación

Hecho:
  ✅ Análisis de onboarding (usuario nuevo se pierde)
  ✅ Análisis de persistencia (qué guardar, qué no)
  ✅ Análisis de Radar (herramienta vs feature vs público)
  ✅ 3 opciones estratégicas claras

En progreso:
  NADA (es análisis, no ejecución)

Bloqueos / riesgos:
  - Onboarding: usuario nuevo confundido si no mejora
  - Radar: puede parecer incompleto sin observatorio
  - Persistencia: decisión afecta E2+

Siguiente paso recomendado:
  OPCIÓN 1 (Onboarding) + OPCIÓN 2 (Radar público)
  Paralelo, no secuencial

═════════════════════════════════════════════════════════════════════════════

SÍNTESIS:

PWR hoy funciona. A.B.D.E0.E1 están cerrados.

Siguiente nivel no es "más features técnicas".
Es "pulir experiencia" + "ganar visibilidad".

OPCIÓN 1: Onboarding → usuario nuevo no se pierde.
OPCIÓN 2: Radar público → PWR es visible externamente.
OPCIÓN 3: Observatorio → usuario ve su historia (después).

HACER AHORA: 1 + inicio de 2.
ESPERAR A: Feedback real antes de 3.

═════════════════════════════════════════════════════════════════════════════
```

---

## DECISIÓN QUE NECESITA ALBERT

1. **¿Aprobas Opción 1 (Onboarding) como siguiente paso?**
   - Afecta visibilidad de PWR, no añade features
   - Es "debt de UX" acumulada

2. **¿Paralelizas con Opción 2 (Radar público)?**
   - Ganas posicionamiento sin costo técnico alto
   - ¿O esperas a tener Opción 1 solid?

3. **¿Qué esperas de Opción 3?**
   - ¿Observatorio es "diferenciador" o "nice to have"?
   - ¿Cuándo sentiría el usuario que "faltan" esas métricas?

4. **Feedback sobre "pendiente de validación visual"**
   - ¿Cuándo puedes probar E1 en entorno real?
   - ¿Hay blockers para empezar Opción 1 mientras tanto?
