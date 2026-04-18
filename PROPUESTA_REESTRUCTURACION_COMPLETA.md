# PROPUESTA COMPLETA: REESTRUCTURACIÓN UX/UI DE PWR

**Fecha**: 2026-04-18
**Status**: Propuesta en revisión
**Criterio de aceptación**: ¿Se puede seguir el trabajo sin confusión? ¿Se refuerza PROYECTO → Tarea → Propuesta → Ejecutar → Resultado? ¿PWR se siente como sistema de trabajo?

---

## 1. MAPA CANÓNICO DE ESTADOS DEL PRODUCTO

PWR tiene exactamente **6 estados nucleares**. Ninguno más, ninguno menos.

| Estado | Cuándo entra | Cuándo sale | Dónde vive |
|--------|-------------|-----------|-----------|
| **Onboarding** | Primera visita o reset | Usuario completa primer éxito | App remoto (no persiste) |
| **Home / Workspace** | Después onboarding; usuario abre app | Usuario elige proyecto o nueva tarea | Pantalla principal |
| **Nueva Tarea** | Usuario toca "Nueva tarea" en Home | Usuario ejecuta o descarta | Pantalla modal/fullscreen limpia |
| **Propuesta Activa** | Router analiza y sugiere | Usuario acepta, rechaza o modifica | En contexto de Nueva Tarea |
| **Resultado Activo** | Ejecución exitosa o con error | Usuario guarda, continúa, o vuelve | Pantalla post-ejecución |
| **Proyecto / Historial** | Usuario toca proyecto en Home | Usuario vuelve a Home o Nueva Tarea | Pantalla secundaria |

**Lo que NO tiene estado propio**: Radar, Settings, Observatorio, Analytics. Todavía no.

---

## 2. OBJETIVO DE CADA ESTADO

### **Onboarding**
**Pregunta que responde**: "¿Cómo funciona esto?"
**Intención dominante**: Primer éxito sin fricción
**Restricción**: Máximo 2 pantallas. Sin wizard pesado.

### **Home / Workspace**
**Pregunta que responde**: "¿Qué hice? ¿Qué puedo retomar? ¿Cómo lanzar algo nuevo?"
**Intención dominante**: Memoria útil del trabajo. Punto de salida.
**Restricción**: Mostrar proyectos recientes + últimas tareas + botón "Nueva Tarea". Nada más.

### **Nueva Tarea**
**Pregunta que responde**: "¿Qué voy a hacer ahora?"
**Intención dominante**: Captura clara de tarea. Nada compite.
**Restricción**: Campo de texto, selector de proyecto, botón "Ver propuesta". Todo lo demás invisible.

### **Propuesta Activa**
**Pregunta que responde**: "¿Cómo sugiere PWR resolverlo?"
**Intención dominante**: Decisión informada antes de ejecutar.
**Restricción**: Modo + Modelo + Motivo visible. Alternativas si usuario lo pide. Un botón: "Ejecutar".

### **Resultado Activo**
**Pregunta que responde**: "¿Qué pasó? ¿Qué hago ahora?"
**Intención dominante**: Resultado visible, guardado, continuidad clara.
**Restricción**: Output, modelo usado, siguiente acción obvia. No hay jerarquía competencia.

### **Proyecto / Historial**
**Pregunta que responde**: "¿Qué tareas contiene este proyecto? ¿Cuál ejecuto o retomo?"
**Intención dominante**: Contexto del proyecto + lista de tareas con estado.
**Restricción**: Nombre proyecto, descripción, lista de tareas recientes/activas/completadas. Opcional: assets generados.

---

## 3. ACCIÓN PRINCIPAL POR ESTADO

Cada estado tiene UNA acción que el usuario espera hacer. Puntería clara. Sin alternativas competencia.

| Estado | Acción Principal | Botón | Visibilidad |
|--------|-----------------|-------|-------------|
| Onboarding | "Crear mi primer proyecto y tarea" | CTA único | Protagonista |
| Home | "Abrir proyecto reciente O crear nueva tarea" | Toggle: Proyectos \| Nueva Tarea | Dual, pero clara separación |
| Nueva Tarea | "Escribir título y descripción" | Siguiente: "Ver propuesta" | Input + botón |
| Propuesta Activa | "Ejecutar con la propuesta de PWR" | "Ejecutar" | Protagonista |
| Resultado Activo | "Guardar como Asset y continuar" | "Guardar" | Protagonista |
| Proyecto | "Seleccionar tarea para retomar o ver detalles" | Click tarea \| "Nueva tarea en este proyecto" | Secundaria |

---

## 4. ELEMENTOS POR ESTADO: QUÉ VIVE DÓNDE

### **Onboarding**

**Visible:**
- Logo/marca PWR (mínimo)
- Texto: "PWR estructura tu trabajo con múltiples LLMs"
- Un campo: "Nombre del proyecto"
- Un campo: "Tu primera tarea"
- CTA: "Empezar"

**Invisible:**
- Home, proyecto, historial, radar, settings
- Propuestas, ejecuciones anteriores
- Cualquier detalle del router

---

### **Home / Workspace**

**Visible:**
- Header mínimo: Logo + "PWR" + (usuario si hay)
- Dos secciones:
  - **Proyectos recientes**: 3-4 tarjetas. Click = abre proyecto. Nombre + última tarea ejecutada + timestamp
  - **Nueva Tarea**: Campo prominente "¿Qué tarea tienes hoy?" + botón "Crear"
- Footer discreto: "Proyectos completos" link si hay historial largo

**Invisible:**
- Sidebar
- Navbar horizontal larga
- Accesos a settings, analytics, observatorio
- Detalles de router, modelos, histórico detallado
- Propuestas activas de trabajos anteriores

**Persistencia visible:**
- Timestamp de última ejecución por proyecto
- Indicador visual: proyecto vacío vs. proyecto con tareas completadas

---

### **Nueva Tarea**

**Visible:**
- Breadcrumb compacto: "PWR > Proyecto: [nombre]" (o "Sin asignar" si no eligió)
- Campo de texto grande: "Título de la tarea"
- Campo más pequeño: "Descripción / contexto"
- Selector: "¿A qué proyecto pertenece?" (si no lo eligió desde Home)
- Botón protagonista: "Ver propuesta"

**Invisible:**
- Home, proyectos, historial
- Router, modelos, modo/eco/racing
- Archivos cargados (todavía; Hito 3)
- Propuestas automáticas (se generan después de "Ver propuesta")

**Jerarquía:**
```
Proyecto: [nombre]
─────────────────────
Título de la tarea: [input grande]
Descripción: [input secundario]

[Ver propuesta]
```

---

### **Propuesta Activa**

**Visible:**
- Breadcrumb: "PWR > Proyecto > Tarea > Propuesta"
- Recapitulación de tarea (read-only)
- **Bloque de decisión** (estructura fija):
  ```
  RECOMENDACIÓN DE PWR
  ───────────────────
  Modo:   ECO
  Modelo: Gemini 2.5 Flash Lite
  Por qué: Tarea directa, prioridad rapidez.
           ~2s, coste estimado <$0.01

  [Ver alternativas] [Ejecutar]
  ```
- Si usuario toca "Ver alternativas":
  - Lista 2-3 opciones: EQUILIBRIO, RACING
  - Cada una: Modo | Modelo | Tiempo | Coste | Precisión estimada
  - Click en una = cambia la propuesta principal
  - Vuelve a "Ejecutar" (solo una opción visible a la vez)

**Invisible:**
- Home, proyecto, historial
- Spinner, loader (aparece solo al ejecutar)
- Copy explicativo adicional
- Detalles del router, reasoning (white box aparece DESPUÉS)

---

### **Resultado Activo**

**Visible:**
- Breadcrumb: "PWR > Proyecto > Tarea > Resultado"
- Recapitulación: Tarea, Proyecto
- **Output principal**: Texto del resultado (seleccionable, copiable)
- **Bloque de metadata**:
  ```
  EJECUCIÓN COMPLETADA
  ───────────────────
  Modelo usado: Gemini 2.5 Flash Lite (ECO)
  Tiempo:       1.8s
  Coste:        $0.004
  ```
- **Siguiente acción obvia**:
  ```
  [Guardar como Asset] [Mejorar análisis] [Nueva tarea] [Proyecto]
  ```
- Si usuario toca "Mejorar análisis":
  - Propuesta: RACING mode (lado a lado)
  - Usuario elige: mantener eco o adoptar racing
  - Si adopta: guarda nuevo resultado, actualiza coste total

**Invisible:**
- Home, otros proyectos
- Spinner de ejecución (ya completó)
- Opciones de modo/modelo (ya se ejecutó)
- Settings, radar, analytics

---

### **Proyecto / Historial**

**Visible:**
- Breadcrumb: "PWR > Proyecto: [nombre]"
- Contexto del proyecto: Nombre + descripción + tags (read-only)
- Lista de tareas:
  - Estado: pendiente, en progreso, completada
  - Título, timestamp de creación
  - Última acción ejecutada (si la hay)
  - Click = abre Resultado si completada, o Nueva Tarea si pendiente
- Botón "Nueva tarea en este proyecto"

**Invisible:**
- Home, otros proyectos
- Radar, settings
- Detalles del router
- Toda la metadata de ejecución (se ve solo en Resultado)

---

## 5. EXPRESIÓN DE LA JERARQUÍA: PROYECTO → TAREA → PROPUESTA → EJECUTAR → RESULTADO

### **Cuándo se ve COMPLETA**
```
PWR > Proyecto: Marketing 2026 > Tarea: Resumir análisis > Propuesta > Ejecutar > Resultado

PROYECTO: Marketing 2026
Contexto: Análisis de tendencias Q1
─────────────────────────────────

TAREA: Resumir análisis competitivo
Descripción: Extrae insights clave del documento PDF

PROPUESTA DE PWR:
Modo:   ECO
Modelo: Gemini 2.5 Flash Lite
Por qué: Tarea estructurada, prioridad rapidez

[Ejecutar]

───────────────────────────────────

RESULTADO:
[Output aquí]

Modelo usado: Gemini 2.5 Flash Lite
Tiempo: 1.8s
Coste: $0.004

[Guardar como Asset] [Mejorar] [Nueva tarea]
```

### **Cuándo se ve PARCIAL**

**Onboarding** → Solo Proyecto + Tarea inicial
```
Mi primer proyecto > Mi primera tarea
```

**Home** → Solo Proyecto (lista) + opción Nueva Tarea (sin Proyecto asignado)
```
[Proyectos recientes] [Nueva Tarea]
```

**Nueva Tarea** → Proyecto + Tarea (sin Propuesta)
```
Proyecto: [nombre] > Tarea: [nuevo]
```

**Propuesta** → Proyecto + Tarea + Propuesta (sin Ejecutar aún)
```
Proyecto > Tarea > Propuesta
```

### **Cómo se marca el paso ACTUAL**

No con números (❌ 1. 2. 3.)
No con barras de progreso (❌ ████░░░░)
No con colores decorativos (❌ circlos rellenos)

**Sí con:**
- Breadcrumb sobrio: "PWR > Proyecto > Tarea > [Propuesta] ← **AQUÍ ESTÁS**"
- Estado visual mínimo: Texto "PROPUESTA" con fondo muy sutil (gris claro, no color)
- Botón protagonista claro: "Ejecutar" o "Guardar" (el botón principal define dónde estás)

### **Cómo se sugiere el SIGUIENTE PASO**

**Visibilidad natural:**
- Después Onboarding → Home aparece. Usuario ve proyectos.
- Después Nueva Tarea → "Ver propuesta" (botón siguiente)
- Después Propuesta → "Ejecutar" (botón siguiente)
- Después Resultado → Cuatro opciones, una es protagonista según contexto:
  - Si es nuevo asset sin guardar → "Guardar como Asset" protagonista
  - Si ya guardado → "Nueva tarea" protagonista
  - "Mejorar análisis" siempre visible (pero secundaria)

**Sin wizard pesado:**
- No hay modales diciendo "paso 3 de 5"
- No hay tooltips explicativos en cada pantalla
- No hay numeritos decorativos

---

## 6. QUÉ SUSTITUYE AL MENÚ LATERAL

El sidebar muere completamente. Su propósito se distribuye así:

### **Header Mínimo (reemplaza orientación global)**

```
[Logo] PWR                    [Usuario] [Salir]
─────────────────────────────────────────────────

Breadcrumb contextual:
PWR > Proyecto: [nombre] > Tarea: [nombre] > [Estado actual]
```

**Criterios:**
- Logo + nombre = marca
- Breadcrumb = orientación ("dónde estoy")
- Usuario + Salir = necesario pero invisible hasta hover

**Ancho máximo**: Breadcrumb no debe romper. Si muy larga, truncar proyecto con "..." + tooltip al hover.

### **Contexto / Información Actual**

En cada estado, el contexto vive donde relevante:
- Proyecto: En el bloque superior como "Proyecto: [nombre]"
- Tarea: En la descripción visible
- Modelo usado: En el bloque de metadata (DESPUÉS ejecución)

### **Breadcrumb Sobrio**

```
PWR > Proyecto > Tarea > Estado actual
```

**Reglas:**
- Click en "Proyecto" = abre Proyecto (vuelve a historial)
- Click en "Tarea" = vuelve a Propuesta (si aún no ejecutada)
- Estado actual NO es clickeable (es read-only, marca dónde estás)
- Sin decoración (flechas mínimas, sin > ornamentales)

**Versión compacta** (si pantalla es pequeña):
```
PWR / Proyecto / Tarea / Resultado
```

### **Navegación Local**

Cada estado tiene sus propias acciones:

| Estado | Navegación local |
|--------|-----------------|
| Home | Click proyecto = abre Proyecto \| "Nueva Tarea" = Nueva Tarea |
| Nueva Tarea | "Ver propuesta" = Propuesta \| "Cancelar" = Home |
| Propuesta | "Ejecutar" = Resultado \| "Cancelar" = Home |
| Resultado | "Guardar" / "Mejorar" / "Nueva tarea" / "Proyecto" = [cada uno] |
| Proyecto | Click tarea = Resultado \| "Nueva tarea" = Nueva Tarea en este proyecto |

**No hay navegación que saltee estados.**

### **Volver (Back)**

Botón de retroceso (←) **solo** en estos casos:
- Nueva Tarea → vuelve a Home
- Propuesta → vuelve a Home (cancela la propuesta)
- Proyecto → vuelve a Home

**No hay back infinito.** El sistema tiene una dirección clara: Home → Proyecto/Nueva Tarea → Propuesta → Resultado → Asset/Nueva Tarea.

### **Acceso a Radar (sin robar foco)**

Radar NO debe ser navegación principal. Es observatorio secundario.

**Ubicación**: Link discreto en footer (versión Home) o en un icono de menú flotante muy pequeño (esquina inferior derecha, sin robar espacio).

```
Home:
[Proyectos] [Nueva Tarea]
────────────────────────────────
...
────────────────────────────────
[Radar] [Config] (links discretos, no botones)
```

**O mejor**: Radar es una pestaña secundaria dentro de Proyecto, no navegación global.

---

## 7. MODO + MODELO + MOTIVO: EXPRESIÓN CONCRETA

### **Dónde aparece**

**Propuesta Activa** (SIEMPRE visible, siempre igual):
```
RECOMENDACIÓN DE PWR
───────────────────
Modo:   ECO
Modelo: Gemini 2.5 Flash Lite
Por qué: Tarea estructurada, prioridad rapidez.
         Tiempo estimado: ~2s | Coste: <$0.01
```

**Resultado Activo** (SIEMPRE visible):
```
EJECUCIÓN COMPLETADA
───────────────────
Modelo usado: Gemini 2.5 Flash Lite (ECO)
Tiempo:       1.8s
Coste:        $0.004
```

### **Con qué jerarquía**

**Estructura fija** (nunca cambiar):
```
LABEL
───────────────────
Modo:   [ECO | EQUILIBRIO | RACING]
Modelo: [Nombre modelo concreto]
Por qué: [1-2 líneas, humano, optional o desplegable]
```

**Tamaño de fuente:**
- Label: pequeño, discreto (12-13px)
- Modo: medio (14-15px)
- Modelo: **grande, protagonista** (16-18px)
- Por qué: pequeño, secundario (12px)

### **Cuándo el motivo va VISIBLE**

**Visible en línea** (sin click):
- Tarea muy clara, sin ambigüedad (ej: clasificar, formatear, traducir)
- Usuario ya confía en PWR
- Una línea breve es suficiente

```
Por qué: Tarea clara, prioridad rapidez
```

### **Cuándo el motivo queda detrás de un CLICK**

El motivo expandido (2-3 líneas + detalles técnicos) aparece si:
- Usuario toca "Por qué" o un icono de info (ℹ)
- O es la primera tarea del usuario (mejor explicar)

**Modal mínimo:**
```
¿Por qué esta recomendación?

La tarea es: [descripción]

Complejidad detectada: Media
Prioridad inferida: Rapidez > Precisión
Modelos disponibles:
  • ECO (recomendado): rápido, barato
  • EQUILIBRIO: balanceado
  • RACING: máxima precisión, más coste

Tu elección: ECO ✓
```

### **Cómo evitar que "ECO/RACING" sea abstracción vacía**

**Regla 1:** Nunca mostrar modo sin modelo concreto.
✅ Correcto: "ECO | Gemini 2.5 Flash Lite"
❌ Incorrecto: "ECO" solo

**Regla 2:** Vincular modo a garantías reales.

```
ECO
├─ Latencia: < 5s (observable)
├─ Precisión: 85-92% (según benchmarks)
├─ Coste: $0.001-0.01 (real)
└─ Modelo: Gemini 2.5 Flash Lite

EQUILIBRIO
├─ Latencia: 3-10s
├─ Precisión: 92-97%
├─ Coste: $0.01-0.05
└─ Modelo: Claude 3.5 Sonnet / Gemini 2.5 Pro

RACING
├─ Latencia: 10-30s
├─ Precisión: 97-99%
├─ Coste: $0.05-0.2
└─ Modelo: Claude Opus 4.6
```

**Regla 3:** El usuario ve modelo concreto ANTES de ejecutar. Siempre.

**Regla 4:** Post-ejecución, mostrar modelo realmente usado (puede divergir si fallback automático).

---

## 8. PERSISTENCIA VISIBLE

### **Guardado Post-Resultado**

Cuando usuario ejecuta una tarea y obtiene resultado:

**Automático (sin click):**
- Task guardada en DB (estado: "completada")
- Resultado guardado (llm_output)
- Metadata guardada (modelo, coste, latencia)
- Timestamp registrado

**Explícito (requiere click):**
```
RESULTADO COMPLETADO
───────────────────
[Output]

Modelo usado: Gemini 2.5 Flash Lite
Tiempo: 1.8s | Coste: $0.004

[Guardar como Asset] [Mejorar análisis] [Nueva tarea]
```

Usuario toca "Guardar como Asset" → Asset creado, visible en Proyecto después.

### **Home con Memoria Útil**

Home no es "Estado vacío hasta que usuario actúe". Home es **workspace vivo**.

**Que muestra:**
- **Proyectos recientes** (últimos 5 abiertos):
  - Nombre proyecto
  - Última tarea ejecutada (título + timestamp "hace 2 horas")
  - Click abre Proyecto

- **Tareas activas** (últimas 3 sin completar):
  - Proyecto | Tarea | Estado (pendiente/en progreso)
  - Click abre Propuesta o Resultado según contexto

- **CTA Nueva Tarea**: Campo input + botón

**Ejemplo:**
```
HOME / WORKSPACE
─────────────────────────────────

PROYECTOS RECIENTES
Marketing 2026    Última: Resumir análisis (hace 2h)    [Abrir]
Product Roadmap   Última: Priorizar features (ayer)      [Abrir]
Research 2026     Última: Extraer insights (hace 3d)    [Abrir]

TAREAS ACTIVAS
Marketing 2026 > Competidores Q1       [Pendiente]
Product Roadmap > Roadmap 2026-2027    [En progreso]

[Nueva tarea] → "¿Qué tarea tienes hoy?"
```

### **Proyecto con Estructura Clara**

Cuando usuario abre Proyecto:

```
PROYECTO: Marketing 2026
Contexto: Análisis de tendencias Q1 2026
─────────────────────────────────────────

TAREAS (3 completadas, 1 pendiente)

Completadas:
✓ Resumir análisis competitivo    [hace 2h]
✓ Extraer insights clave         [ayer]
✓ Generar recomendaciones        [2 días atrás]

Pendientes:
○ Diseñar roadmap de acciones    [Actualizado hace 1h]

[Nueva tarea en este proyecto]
```

Click en tarea completada → ve Resultado
Click en tarea pendiente → continúa o edita Propuesta

### **Continuidad Real**

Usuario vuelve a la app 3 días después:

1. Home muestra proyectos recientes (Marketing 2026 visible)
2. Toca Marketing 2026
3. Ve todas sus tareas, timestamps, estado
4. Toca una pendiente → propuesta aparece (misma que hace 3 días)
5. O retoma resultado completado → puede copiar, mejorar, guardar versión nueva

**Sin necesidad de buscar, navegar complejos, o preguntar "¿dónde estaban mis cosas?"**

---

## 9. SECUENCIA DE IMPLEMENTACIÓN (PRIORIZADA Y RAZONADA)

### **Hito A: Estructura Base (Semana 1-2)**

**Implementar:**
1. Header mínimo (logo + breadcrumb + usuario/salir)
2. Home rediseñado (proyectos recientes + Nueva Tarea)
3. Eliminar sidebar completamente
4. Rutas claras: Home → Proyecto / Nueva Tarea → Propuesta → Resultado

**Razón:** Sin esta estructura, todo lo demás se apila sobre confusión.
**Risk:** Cambio visual fuerte; usuarios notan inmediatamente.
**Validación:** Tres tareas de prueba. ¿Usuario sabe dónde está sin confusión?

---

### **Hito B: Propuesta Clara (Semana 2-3)**

**Implementar:**
1. Bloque "RECOMENDACIÓN DE PWR" con Modo | Modelo | Por qué
2. "Ver alternativas" → lista 2-3 opciones con latencia/coste
3. Estado Propuesta visual: breadcrumb marca "Propuesta" claramente

**Razón:** Core de PWR. Usuario debe confiar antes de ejecutar.
**Risk:** Si la propuesta no es clara, ejecución es ciega.
**Validación:** Usuario ve modelo concreto ANTES de ejecutar. Punto.

---

### **Hito C: Resultado y Persistencia (Semana 3-4)**

**Implementar:**
1. Bloque "EJECUCIÓN COMPLETADA" con modelo usado + tiempo + coste
2. Botón "Guardar como Asset" funcional
3. Home muestra tareas activas + recientes
4. Proyecto muestra todas tareas con estado

**Razón:** Sin persistencia visible, usuario siente que se pierde el trabajo.
**Risk:** SQL queries deben ser eficientes (Home carga muchos datos).
**Validación:** Usuario vuelve al día siguiente. Sus tareas están. ¿Tiene continuidad?

---

### **Hito D: Onboarding Limpio (Semana 4)**

**Implementar:**
1. Primera pantalla: nombre proyecto + tarea inicial
2. Router propone. Usuario ejecuta.
3. Resultado es Asset automático
4. Home aparece. Ciclo completo.

**Razón:** Primer usuario debe llegar a "primer resultado" en < 2 minutos.
**Risk:** UX debe ser obvious. Sin instrucciones.
**Validación:** Usuario nuevo, sin explicaciones. ¿Llega a un resultado útil?

---

### **Hito E: Mejorar con Análisis (Semana 5)**

**Implementar:**
1. Resultado: Botón "Mejorar análisis" → propuesta RACING
2. Lado a lado: ECO vs RACING
3. Usuario elige: mantener o adoptar
4. Nuevo resultado guardado con actualización de coste

**Razón:** Ya funciona, solo refinar UX.
**Risk:** Comparación lado a lado debe ser clara.
**Validación:** Usuario entiende qué mejora.

---

### **Lo que puede esperar (Hito 6 onwards):**
- Multimodal input (Hito 6)
- Multi-proveedor (Hito 7)
- Radar / Analytics (Hito 8+)
- Colaboración (Hito 9+)

---

## 10. VALIDACIÓN CONTRA CRITERIOS

### **¿Sin leer demasiado, el siguiente paso es evidente?**

✅ Home → "Proyectos" o "Nueva Tarea". Click.
✅ Nueva Tarea → "Ver propuesta". Click.
✅ Propuesta → "Ejecutar". Click.
✅ Resultado → Cuatro opciones, una es prominente según contexto.

**Criterio pasado.** El flujo es lineal. Usuario no se pierde.

---

### **¿Refuerza la secuencia PROYECTO → TAREA → PROPUESTA → EJECUTAR → RESULTADO?**

✅ Breadcrumb siempre visible: "PWR > Proyecto > Tarea > [Estado actual]"
✅ Cada estado es una pantalla. No hay jerarquía competencia.
✅ Proyecto es contexto superior en Home, Nueva Tarea, Resultado.

**Criterio pasado.** La jerarquía es evidente. Proyecto es primero.

---

### **¿Hace que PWR se sienta más como sistema de trabajo y menos como panel confuso?**

✅ Sidebar muere. Menos visual noise.
✅ Una acción principal por estado. Menos opciones competencia.
✅ Persistencia visible. Sensación de memoria útil.
✅ Modo + Modelo + Motivo concretos. Decisiones no son abstracciones.

**Criterio pasado.** PWR se siente como workspace, no como app genérica.

---

## STATUS TECH

### **Objetivo Actual**
Estructuración clara de PWR: eliminar confusión de navegación, reforzar secuencia canónica, hacer modo/modelo explícito.

### **Hecho** ✅
- Router v1 funcional (Gemini 2.5)
- Decisión eco/racing lógicamente correcta
- Metadata persistida (latencia, coste estimado)
- DB schema limpio (Projects, Tasks, Assets)

### **En Progreso** ⏳
- Propuesta de reestructuración UX (THIS DOCUMENT)

### **Bloqueadores / Riesgos**

| Bloqueador | Impacto | Mitigación |
|-----------|--------|-----------|
| Sidebar queda código legacy (React components) | Deuda técnica | Eliminar completamente, no esconder |
| Home con muchas queries | Performance | Paginar, lazy load proyectos recientes |
| Breadcrumb rompe en pantallas pequeñas | UX en móvil | Versión compacta, truncar con tooltip |
| Usuario confundido post-cambio visual | Adopción | Onboarding claro, no warning/modales |

### **Siguiente Paso Recomendado**

1. **Albert: Revisión y feedback** (48h)
   - ¿Propuesta es dura y accionable?
   - ¿Hay gaps en los 6 estados?
   - ¿La secuencia Hito A-E tiene sentido?

2. **Decisión: Ir / No ir a implementación**
   - Si Sí: Comenzar Hito A (Header + Home) en próxima sesión
   - Si No: Ajustar qué puntos, y re-revisar

3. **Post-aprobación: Especificación técnica detallada**
   - React component map
   - Routes (React Router)
   - DB queries optimizadas
   - Validación de cada estado

### **Decisión que necesita Albert**

> **¿Aprobamos esta estructura como marco de rediseño?**
>
> Si sí: Confirmá, y comenzamos Hito A la próxima sesión (Header + Home).
> Si no: Cuál es el gap principal. Ajustamos y re-enviamos.
>
> **NO quiero** más iteraciones de copy o detalle visual. Quiero green light estructural.

---

**Documento cerrado. Propuesta lista para revisión.**

*Fecha: 2026-04-18 | Versión: 1.0 | Status: Pendiente aprobación Albert*
