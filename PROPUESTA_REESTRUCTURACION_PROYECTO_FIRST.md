════════════════════════════════════════════════════════════════════════════════
PROPUESTA: REESTRUCTURACIÓN DE PWR — PROYECTO FIRST (Sin Sidebar Persistente)
════════════════════════════════════════════════════════════════════════════════

**Status:** PROPUESTA (no implementar aún)
**Principio Guía:** PROYECTO → Tarea → Propuesta → Ejecutar → Resultado
**Restricción:** Sin menú lateral persistente, una acción principal por estado
**Objetivo:** Que la secuencia se SIENTA, no se explique

════════════════════════════════════════════════════════════════════════════════
PARTE 1: REDEFINICIÓN DE ESTADOS
════════════════════════════════════════════════════════════════════════════════

### ESTADO A: Vacío (Primer acceso, sin proyectos)
- **Objetivo:** Crear primer proyecto o traer usuario a onboarding
- **Acción principal:** "Crear proyecto" o "Comenzar con tarea"
- **Header superior:** Ninguno (es estado inicial)
- **Navegación mínima:** 2 opciones claras
- **Persistencia visible:** N/A

---

### ESTADO B: Proyecto Seleccionado — Vista de Tareas
- **Objetivo:** Ver y seleccionar tarea a trabajar
- **Dónde en secuencia:** PROYECTO ← usuario está aquí
- **Acción principal:** Seleccionar tarea existente O crear nueva
- **Header superior:**
  ```
  [Proyecto: Mi Proyecto]
  ```
- **Navegación mínima:** Volver a home, crear nueva tarea, cambiar proyecto
- **Persistencia visible:**
  - ✅ Ejecutadas (con badge "Resultado disponible")
  - 📌 Pendientes

---

### ESTADO C: Proyecto + Tarea Seleccionada — Vista de Propuesta
- **Objetivo:** Ver propuesta y decidir ejecutar
- **Dónde en secuencia:** PROYECTO > TAREA → PROPUESTA ← usuario está aquí
- **Acción principal:** "Ejecutar" (botón primario, obvious)
- **Header superior:**
  ```
  [Proyecto: Mi Proyecto] > [Tarea: Resume documento]
  Paso: Propuesta
  ```
- **Navegación mínima:** Volver (a proyecto), editar tarea, cambiar proyecto
- **Persistencia visible:** (viene de bloque H - mostrar contexto guardado)

---

### ESTADO D: Proyecto + Tarea + Ejecución en Progreso
- **Objetivo:** Mostrar progreso y resultado
- **Dónde en secuencia:** PROYECTO > TAREA > PROPUESTA > EJECUTAR → RESULTADO ← usuario está aquí
- **Acción principal:** "Usar resultado" o "Ver en proyecto"
- **Header superior:**
  ```
  [Proyecto: Mi Proyecto] > [Tarea: Resume documento]
  Paso: Resultado
  ```
- **Navegación mínima:** Volver a proyecto, crear tarea relacionada
- **Persistencia visible:**
  - ✅ Guardado / En: [Proyecto] / Tarea: [Nombre] (bloque H)
  - Acciones jerárquicas (Ver, Reutilizar, Copiar)

---

### ESTADO E: Home — Vista de Historial y Proyectos
- **Objetivo:** Navegar rápidamente a trabajo reciente o seleccionar proyecto
- **Dónde en secuencia:** Punto de entrada, fuera de la secuencia
- **Acción principal:** Seleccionar proyecto reciente O crear nuevo
- **Header superior:** Ninguno (es home)
- **Navegación mínima:** Crear proyecto, buscar
- **Persistencia visible:**
  - #### Hoy — 5 últimas ejecuciones (bloque H)
  - #### Proyectos Recientes — quick access

════════════════════════════════════════════════════════════════════════════════
PARTE 2: HEADER SUPERIOR SOBRIO (Jerarquía Visible)
════════════════════════════════════════════════════════════════════════════════

### Principios del Header

1. **Nunca más de 1 línea** (excepto con pequeño detalle debajo)
2. **Proyecto siempre primero**
3. **Contexto + Paso actual**
4. **Sin números, sin barras, sin decoración**
5. **Clickeable para navegar**

---

### Ejemplos por Estado

#### ESTADO B: Proyecto Seleccionado
```
┌─────────────────────────────────────────────────────────────────┐
│ [◀ Volver] · Proyecto: Mi Proyecto                              │
└─────────────────────────────────────────────────────────────────┘

CONTENIDO:
- ✅ Ejecutadas (badge "Resultado disponible")
- 📌 Pendientes
```

**Interpretación:** Usuario ve dónde está (Proyecto), puede volver atrás con un clic.

---

#### ESTADO C: Proyecto + Tarea — Propuesta
```
┌─────────────────────────────────────────────────────────────────┐
│ [◀ Volver] · Proyecto: Mi Proyecto > Tarea: Resume documento   │
│ Paso actual: Propuesta (Decidir)                               │
└─────────────────────────────────────────────────────────────────┘

CONTENIDO:
[Propuesta de cómo resolver]
[Botón primario: ✨ Ejecutar]
```

**Interpretación:** Usuario sabe exactamente dónde está, qué paso es (Propuesta),
qué hacer (botón grande Ejecutar).

---

#### ESTADO D: Proyecto + Tarea — Resultado
```
┌─────────────────────────────────────────────────────────────────┐
│ [◀ Volver] · Proyecto: Mi Proyecto > Tarea: Resume documento   │
│ Resultado disponible                                             │
└─────────────────────────────────────────────────────────────────┘

CONTENIDO:
[Resultado de la ejecución]

✅ Guardado
En: **Mi Proyecto**
Tarea: **Resume documento**

[📂 Ver en proyecto] [🔄 Reutilizar] [🎯 Nueva tarea]
```

**Interpretación:** Usuario ve resultado, sabe que está guardado, acción obvia es
"Ver en proyecto" o crear nueva tarea.

════════════════════════════════════════════════════════════════════════════════
PARTE 3: NAVEGACIÓN MÍNIMA (Sin Sidebar)
════════════════════════════════════════════════════════════════════════════════

### Principio
**Un botón "Volver" siempre disponible. Nada más persistente.**

### Por Estado

#### ESTADO B (Proyecto Seleccionado)
```
HEADER: [◀ Volver] · Proyecto: Mi Proyecto
BOTONES INLINE:
  - [➕ Nueva tarea] (bajo la lista de tareas)
  - [⚙️ Cambiar proyecto] (botón discreto arriba)
ACCIONES:
  - Clic en tarea → ESTADO C
  - "Nueva tarea" → formulario inline
  - "Volver" → ESTADO E (Home)
```

#### ESTADO C (Propuesta)
```
HEADER: [◀ Volver] · Proyecto > Tarea · Paso: Propuesta
BOTONES:
  - [✨ Ejecutar] (PRIMARIO, obvious)
  - [Editar] (discreto)
ACCIONES:
  - "Ejecutar" → ESTADO D
  - "Volver" → ESTADO B
```

#### ESTADO D (Resultado)
```
HEADER: [◀ Volver] · Proyecto > Tarea · Resultado disponible
BOTONES:
  - [📂 Ver en proyecto] (PRIMARIO, obvious)
  - [🔄 Reutilizar] (SECUNDARIO)
  - [🎯 Nueva tarea] (SECUNDARIO)
ACCIONES:
  - "Ver en proyecto" → ESTADO B
  - "Reutilizar" → ESTADO C (con contexto pre-filled)
  - "Nueva tarea" → ESTADO C (nueva)
  - "Volver" → ESTADO B
```

#### ESTADO E (Home)
```
HEADER: ninguno
CONTENIDO:
  #### Hoy
  [5 últimas ejecuciones con timestamp]

  #### Proyectos Recientes
  [3-4 proyectos con último acceso]

BOTONES:
  - [➕ Crear proyecto] (formulario modal)
  - [🔍 Buscar] (dropdown con historial)
ACCIONES:
  - Clic en proyecto → ESTADO B
  - Clic en tarea en "Hoy" → ESTADO C (directo a propuesta)
```

════════════════════════════════════════════════════════════════════════════════
PARTE 4: PERSISTENCIA VISIBLE (Sin Sidebar)
════════════════════════════════════════════════════════════════════════════════

### Dónde Aparece

#### En ESTADO B (Proyecto)
```
Separación clara de tareas:
├── ✅ Ejecutadas
│   └─ Resume documento [📋 Resultado disponible]
│   └─ Escribe email [📋 Resultado disponible]
└── 📌 Pendientes
    └─ Analiza gráfico
```

**Beneficio:** User ve de un vistazo qué se completó y qué falta.

---

#### En ESTADO D (Resultado)
```
✅ Guardado
En: **Mi Proyecto**
Tarea: **Resume documento**

Acciones jerárquicas claras:
[📂 Ver en proyecto] ← PRIMARY
[🔄 Usar contexto] [🎯 Nueva relacionada] ← SECONDARY
▼ 📋 Copiar ← TERTIARY
```

**Beneficio:** User siente que trabajo está seguro, sabe dónde volver.

---

#### En ESTADO E (Home)
```
#### Hoy
✅ Resume documento
   Mi Proyecto · hace 10 minutos · [→]

✅ Escribe email
   Mi Proyecto · hace 1 hora · [→]

#### Proyectos Recientes
📁 Mi Proyecto (última actividad: hoy)
📁 Otro Proyecto (última actividad: hace 2 días)
```

**Beneficio:** User ve inmediatamente qué hizo, dónde, cuándo. Timeline natural.

════════════════════════════════════════════════════════════════════════════════
PARTE 5: DIAGRAMA DE FLUJO (Estados + Acciones)
════════════════════════════════════════════════════════════════════════════════

```
ESTADO E (Home)
├─ Mostrar "Hoy" (últimas ejecuciones)
├─ Mostrar Proyectos Recientes
└─ Acciones: Clic proyecto → B, Clic tarea en "Hoy" → C

       ↓ clic en proyecto

ESTADO B (Proyecto Seleccionado)
├─ Header: "Proyecto: X"
├─ Mostrar ✅ Ejecutadas | 📌 Pendientes
├─ Acción principal: seleccionar tarea
└─ Acciones: Clic tarea → C, Volver → E, Nueva tarea → C (new)

       ↓ clic en tarea existente
       ↓ clic en "Nueva tarea"

ESTADO C (Propuesta)
├─ Header: "Proyecto > Tarea | Paso: Propuesta"
├─ Mostrar propuesta de cómo resolver
├─ Acción principal: Ejecutar
└─ Acciones: Ejecutar → D, Volver → B, Editar

       ↓ Ejecutar

ESTADO D (Resultado)
├─ Header: "Proyecto > Tarea | Resultado disponible"
├─ Mostrar resultado
├─ Bloque "Guardado en" (H visible)
├─ Acción principal: Ver en proyecto
└─ Acciones: Ver → B, Reutilizar → C, Nueva → C, Volver → B
```

════════════════════════════════════════════════════════════════════════════════
PARTE 6: CAMBIOS vs ESTADO ACTUAL (Bloque H)
════════════════════════════════════════════════════════════════════════════════

### Qué Cambia
```
ANTES (Actual con sidebar):
  Proyecto + Tarea           [Sidebar izquierda + Contenido derecha]
  (Sidebar siempre visible)  (25% espacio + 75% contenido)

DESPUÉS (Propuesta):
  Proyecto + Tarea           [Header superior + Contenido fullwidth]
  (Sin sidebar)              (Jerarquía en header + 100% contenido)
```

---

### Qué No Cambia
```
✅ Router logic (eco/racing decision engine)
✅ Execution pipeline
✅ Bloque H (Persistencia Visible)
✅ Backend BD (sin cambios)
✅ Estados A-D (mismo flujo, otra presentación)
```

---

### Qué se Reemplaza
```
❌ Sidebar layout (25% espacio robado)
→ ✅ Header minimal + fullwidth content

❌ Duplicación de contexto (sidebar + main)
→ ✅ Contexto en header, contenido limpio

❌ "Tareas activas" sin visibilidad de ejecutadas/pendientes
→ ✅ Separación clara (bloque H)
```

════════════════════════════════════════════════════════════════════════════════
PARTE 7: CÓMO SE SIENTE LA SECUENCIA (Sin Explicación)
════════════════════════════════════════════════════════════════════════════════

### Flujo Natural del User

```
1️⃣ Abre PWR
   ↓ "¿Qué hago?" Ve "Hoy" (últimas tareas)
   ↓ Clica en tarea ejecutada

2️⃣ Se abre ESTADO C (Propuesta)
   ↓ Encabezado dice: "Proyecto > Tarea | Propuesta"
   ↓ Usuario SIENTE: "Ah, aquí debo decidir si ejecuto"
   ↓ Botón gigante: "Ejecutar"

3️⃣ Clica Ejecutar, ESTADO D (Resultado)
   ↓ Encabezado dice: "Proyecto > Tarea | Resultado"
   ↓ Bloque "Guardado en" es visible
   ↓ Usuario SIENTE: "Está aquí, seguro, en Mi Proyecto"
   ↓ Botón primario: "Ver en proyecto"

4️⃣ Clica "Ver en proyecto", ESTADO B
   ↓ Encabezado: "Proyecto: Mi Proyecto"
   ↓ Ve ✅ Ejecutadas, 📌 Pendientes
   ↓ Usuario SIENTE: "Aquí está mi trabajo, veo qué completo y qué falta"

5️⃣ Pueden:
   ├─ Ejecutar otra tarea (→ C)
   ├─ Crear nueva tarea (→ C)
   └─ Volver a home (→ E)
```

**Característica:** La secuencia SIENTE lógica. No hay que explicar qué paso es.
El encabezado dice "Proyecto > Tarea | Paso actual" y todo cobra sentido.

════════════════════════════════════════════════════════════════════════════════
PARTE 8: VALIDACIÓN CONTRA PRINCIPIOS
════════════════════════════════════════════════════════════════════════════════

### Checklist de Validación

| Principio | Validación |
|-----------|-----------|
| PROYECTO → Tarea → ... | ✅ Header muestra "Proyecto > Tarea" en cada paso |
| Sin sidebar persistente | ✅ Solo header minimal (1 línea máx) |
| Una acción principal | ✅ Cada estado tiene un botón PRIMARIO obvio |
| Persistencia visible | ✅ Bloque H + separación ejecutadas/pendientes |
| Que se SIENTA, no explique | ✅ Encabezado + botón principal = flujo obvious |
| No requiere scroll horizontal | ✅ Content 100% width sin sidebar |
| Contexto claro | ✅ Siempre sé dónde estoy (header) |
| Siguiente paso obvious | ✅ Un botón primario en cada estado |

════════════════════════════════════════════════════════════════════════════════
PARTE 9: EJEMPLO VISUAL (ASCII) — ESTADO C (Propuesta)
════════════════════════════════════════════════════════════════════════════════

```
┌──────────────────────────────────────────────────────────────────┐
│ [◀] · Proyecto: Mi Proyecto > Tarea: Resume documento           │
│ Paso actual: Propuesta                                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ 🧠 Mi análisis de cómo resolver esto:                           │
│                                                                  │
│ [Propuesta generada por Router...]                              │
│ 1. Entiendo que necesitas resumir un documento                  │
│ 2. Voy a usar estrategia "extracto" (más rápido)               │
│ 3. Modo: eco (eficiencia máxima)                                │
│                                                                  │
│ ┌─ Detalle expandible ─────────────────────────────────────────┐│
│ │ Razonamiento: Documento técnico + 2000 palabras = eco OK     ││
│ └──────────────────────────────────────────────────────────────┘│
│                                                                  │
│ [Editar tarea] [⚙️ Cambiar estrategia]                          │
│                                                                  │
│ ┌───────────────────────────────────────────────────────────────┐│
│ │ ✨ EJECUTAR                                    ← PRIMARIO     ││
│ └───────────────────────────────────────────────────────────────┘│
│                                                                  │
│ [Volver] [Crear otra en proyecto]                               │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

**Lectura:** Usuario ve encabezado → SIENTE dónde está → Ve propuesta →
Ve botón gigante "Ejecutar" → Acción obvious.

════════════════════════════════════════════════════════════════════════════════
PARTE 10: ROADMAP PARA IMPLEMENTACIÓN (Cuando sea)
════════════════════════════════════════════════════════════════════════════════

### Bloque I: Header Superior + Estados Redefinidos
**Qué hacer:**
1. Crear componente `header_navigation()` con lógica de breadcrumb
2. Redefinir los 5 estados (A, B, C, D, E)
3. Remover sidebar completamente de flujos
4. Ajustar main content a 100% width

**Estimado:** 2-3 cambios en app.py, refactor de states

---

### Bloque J: Navegación Mínima + Refinamiento
**Qué hacer:**
1. Implementar "Volver" coherente
2. Ajustar botones por estado (una acción principal clara)
3. Testing de flujo end-to-end
4. Validar que secuencia SIENTE lógica

**Estimado:** Refinamientos en UX/flujo

---

### Bloque K: Persistencia Distribuida (Si aplica)
**Qué hacer:**
1. Replicar persistencia visible en ESTADO E (Home)
2. Añadir "Historial rápido" (proyectos/tareas recientes)
3. Timeline natural (Hoy, Esta semana, Anterior)

**Estimado:** Queries BD + UI nuevas

════════════════════════════════════════════════════════════════════════════════
PARTE 11: DECISIONES PENDIENTES DE APROBACIÓN
════════════════════════════════════════════════════════════════════════════════

### 1. ¿Sidebar completamente ausente o minimizado?
- **Opción A:** Ausente en todos los estados (propuesta actual)
- **Opción B:** Ausente en flujos (C, D), visible en navegación (B, E)
- **Recomendación:** A (ausencia total simplifica cognitive load)

---

### 2. ¿Header clickeable para navegar o solo para contexto?
- **Opción A:** Clickeable (Proyecto y Tarea llevan a vistas anteriores)
- **Opción B:** Solo contexto (botón "Volver" es la navegación)
- **Recomendación:** A (más rápido y directo, menos confuso)

---

### 3. ¿Cuántas líneas máximo para header?
- **Opción A:** 1 línea (Proyecto > Tarea | Paso)
- **Opción B:** 2 líneas (línea 1: contexto, línea 2: paso actual)
- **Recomendación:** B (más legible, sigue siendo sobrio)

---

### 4. ¿Nuevo botón "Cambiar proyecto" o solo via Volver?
- **Opción A:** Botón discreto en header
- **Opción B:** Solo volver a Home → seleccionar otro
- **Recomendación:** B (reduce clutter, flujo más limpio)

════════════════════════════════════════════════════════════════════════════════
RESUMEN EJECUTIVO
════════════════════════════════════════════════════════════════════════════════

### La Propuesta

PWR se reestructura alrededor de la secuencia **PROYECTO → Tarea → Propuesta → Ejecutar → Resultado**, sin sidebar persistente.

### Cómo

- **5 estados claros** (A: Vacío, B: Proyecto, C: Propuesta, D: Resultado, E: Home)
- **Header minimal** que muestra siempre dónde estoy
- **Una acción principal** por estado (botón obvious)
- **Persistencia visible** en cada nivel (Bloque H distribuido)
- **Navegación mínima** ("Volver" + botones contextuales)

### Resultado

La secuencia **SE SIENTE**. No hay que leerla ni explicarla. User entiende:
- Dónde está (header)
- Qué hace aquí (botón primario)
- Qué sigue (acción obvia)

### Próximos pasos

**NO implementar aún.** Esperar aprobación de decisiones pendientes.

Cuando se apruebe, será Bloque I: "Header Superior + Estados Redefinidos".

════════════════════════════════════════════════════════════════════════════════
