# PWR Home - Wireframe Exacto

**Criterio**: Home como punto de retorno al trabajo, no como panel administrativo.

---

## LAYOUT GENERAL

```
┌──────────────────────────────────────────────────────────────────┐
│ HEADER COMPACTO                                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  CONTINUAR TRABAJO RECIENTE         ← BLOQUE 1 (Protagonista)   │
│  ┌────────────────────────────────┐                             │
│  │ Tarea: Explicar algoritmo...   │                             │
│  │ Proyecto: PWR                  │                             │
│  │ Hace 1 hora · ECO              │                             │
│  │ [Continuar] [Más recientes ↓] │                             │
│  └────────────────────────────────┘                             │
│                                                                  │
│  ──────────────────────────────────────────────────────────────  │
│                                                                  │
│  CAPTURA RÁPIDA                    ← BLOQUE 2 (Entrada)        │
│  ┌────────────────────────────────┐                             │
│  │ + Pensar, escribir, programar..│                             │
│  │ (input con ícono)              │                             │
│  └────────────────────────────────┘                             │
│                                                                  │
│  ──────────────────────────────────────────────────────────────  │
│                                                                  │
│  PROYECTOS RECIENTES               ← BLOQUE 3 (Contexto)       │
│  ┌─────────────────┐ ┌─────────────────┐                        │
│  │ PWR             │ │ RosmarOps       │                        │
│  │ 3 tareas        │ │ 5 tareas        │                        │
│  │ Última: hace 1h │ │ Última: ayer    │                        │
│  │ [Abrir]         │ │ [Abrir]         │                        │
│  └─────────────────┘ └─────────────────┘                        │
│                                                                  │
│  ──────────────────────────────────────────────────────────────  │
│                                                                  │
│  [+ Nuevo Proyecto]                ← BLOQUE 4 (Secundaria)     │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## HEADER COMPACTO

```
┌──────────────────────────────────────────────────────────────────┐
│ Portable Work Router                                             │
│ Retoma tu trabajo, captura tareas, usa el mejor modelo          │
└──────────────────────────────────────────────────────────────────┘

DIMENSIONES:
- Altura: ~70px (antes: ~140px)
- Padding: 1rem 1.5rem
- Título: 18px bold, #0F172A
- Subtítulo: 13px muted, #64748B (línea de valor)
- Background: #FFFFFF
- Border-bottom: 1px subtle #F1F5F9

CONTENIDO:
- Título: "Portable Work Router" (marca + producto)
- Subtítulo: "Retoma tu trabajo, captura tareas, usa el mejor modelo"
  * Explica el valor en 1 línea
  * Orienta qué puedes hacer
  * NO son métricas

VISUAL:
- SIN selectbox proyecto
- SIN métricas numéricas (2 / 1 / 0)
- Minimalista, contextual, NO distrae del contenido
```

---

## BLOQUE 1: CONTINUAR TRABAJO RECIENTE

```
CONTINUAR TRABAJO RECIENTE
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  📋 Explicar algoritmo de búsqueda          [PRINCIPAL - activo]│
│  Proyecto: PWR  ·  Pensar  ·  ECO  ·  Hace 1 hora             │
│  [Continuar]                                                    │
│                                                                 │
│  ───────────────────────────────────────────────────────────   │
│                                                                 │
│  📋 Documentar endpoints API                                    │
│  Proyecto: PWR  ·  Escribir  ·  ECO  ·  Ayer                  │
│  [Continuar]                                                    │
│                                                                 │
│  📋 Revisar PR #284                                             │
│  Proyecto: PWR  ·  Revisar  ·  Sonnet  ·  Lunes               │
│  [Continuar]                                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

JERARQUÍA VISUAL:
- PRINCIPAL (primer item):
  * Fondo muy light (#EFF6FF) o accent sutil
  * Título: 15px bold, #0F172A
  * Meta: 12px muted, inline
  * Botón [Continuar]: prominente, azul

- SECUNDARIOS (items 2-3):
  * Fondo #FFFFFF
  * Título: 14px regular
  * Meta: 11px muted
  * Botón [Continuar]: outline

- Padding: 1.25rem per item
- Border: 1px subtle, radio 10px
- Shadow: sutil
- Separator entre items: 1px #F1F5F9

CONTENIDO:
- ESTADO CON ACTIVIDAD: mostrar 2-3 tareas ejecutadas recientes (último mes)
  * Primera con background destacado (es la principal)
  * Resto como contexto secundario
- ESTADO VACÍO: "Todavía no hay tareas ejecutadas"
  * [Capturar primera tarea] link/botón
  * Mensaje: "Comienza capturando una tarea para retomar el trabajo"
```

---

## BLOQUE 2: CAPTURA RÁPIDA

```
CAPTURA RÁPIDA
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│ + Pensar, escribir, programar, revisar, decidir...            │
│ [input]                                                         │
│                                                                 │
│ ⚙️ Opciones     📎 Archivos     🏢 Proyecto                    │
│    (expandible)  (upload)        (selector)                    │
│                                                                 │
│ [Capturar]                                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

JERARQUÍA VISUAL - INPUT:
- Ícono "+" a la izquierda (color #2563EB)
- Placeholder descriptivo
- Borde 2px, focus azul
- Padding: 0.75rem 1rem
- Background #FFFFFF
- Radio 8px

JERARQUÍA VISUAL - OPCIONES DISCRETAS:
- Links pequeños (11px, color #2563EB, underline on hover)
- Alineados horizontalmente bajo input
- NO visible por defecto (o muy sutiles)
- Al click, se expanden inline:
  * "⚙️ Opciones" → Tipo (combo Pensar/Escribir/Programar/Revisar/Decidir) + Descripción (textarea small)
  * "📎 Archivos" → File uploader
  * "🏢 Proyecto" → Selector proyecto (dropdown)

BOTÓN CAPTURAR:
- Visible siempre, abajo del input
- Azul primario, full-width o 50%
- 13px bold
- Disabled si input vacío

COMPORTAMIENTO:
- Input visible siempre (NO modal)
- Opciones se expanden bajo demanda, inline en el bloque
- Flujo: escribe título → [expandir si necesita] → [Capturar]
- Si título vacío, botón disabled
- Al capturar, input se limpia y vuelve a estado collapsed

ENTIDAD: Bloque de entrada clara, sin fricción, sin modales
```

---

## BLOQUE 3: PROYECTOS RECIENTES

```
PROYECTOS RECIENTES
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│ ┌──────────────────────┐  ┌──────────────────────┐              │
│ │ 📁 PWR               │  │ 📁 RosmarOps        │              │
│ │                      │  │                      │              │
│ │ 3 tareas activas     │  │ 5 tareas activas    │              │
│ │ Última: hace 1 hora  │  │ Última: ayer        │              │
│ │                      │  │                      │              │
│ │ [Abrir]        ⭐    │  │ [Abrir]        ⭐    │              │
│ │ (primario)     (fix) │  │ (primario)     (fix) │              │
│ └──────────────────────┘  └──────────────────────┘              │
│                                                                 │
│ [Ver todos →]                                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

JERARQUÍA VISUAL:

CARD:
- Padding: 1.25rem
- Border: 1px subtle (#E2E8F0), radio 10px
- Background: #FFFFFF
- Shadow: 0 1px 3px rgba(15, 23, 42, 0.08)

CONTENIDO:
- Ícono: 📁 (o simple cuadrado con color de proyecto)
- Título proyecto: 14px bold, #0F172A
- Contador: "X tareas activas" (12px muted)
- Última actividad: "Última: hace 1 hora" (11px muted, gris)

BOTONES:
- [Abrir]: PRIMARIO azul, full-width o 70%
  * 13px bold
  * Padding 0.6rem 1rem
  * Click → abre proyecto

- ⭐ : TERCIARIO icon-only (fijar/quitar favorito)
  * 16px icon
  * Click → toggle favorito
  * Sin border, hover sutil background
  * Positioned top-right o inline en fila con Abrir

LAYOUT:
- 2 columnas por defecto (responsive a 1 en mobile)
- Gap: 1rem
- Máximo 2 proyectos visibles sin scroll
- [Ver todos →] link abajo si hay más de 2 proyectos

INFORMACIÓN MÍNIMA:
- Nombre proyecto
- Contador de tareas activas (no ejecutadas)
- Timestamp última actividad
- NO mostrar descripción completa (usa caption si la hay)

ESTADO VACÍO:
- "Todavía no hay proyectos"
- [Crear primer proyecto] link
```

---

## BLOQUE 4: CREAR PROYECTO (SECUNDARIO)

```
[+ Crear nuevo proyecto]

JERARQUÍA VISUAL:
- Botón outline, no sólido
- Centrado o a la izquierda
- 13px bold
- Padding: 0.75rem 1.5rem
- Border 1.5px, color #DBEAFE
- Background: transparent
- Hover: background #EFF6FF

POSICIÓN: Abajo del bloque 3, después de espacio vertical (2rem)

COMPORTAMIENTO:
- Click → Modal/Drawer de crear proyecto (mismo que en UI actual)
- NO es el protagonista, es acción secundaria
```

---

## ESPACIADO GENERAL

```
HEADER
│
├─ 1.5rem gap
│
CONTINUAR RECIENTE
│
├─ 1.5rem gap (separator visual: línea subtle o espacio)
│
CAPTURA RÁPIDA
│
├─ 1.5rem gap (separator)
│
PROYECTOS RECIENTES
│
├─ 2rem gap (más respiro)
│
CREAR PROYECTO

PADDING GENERAL:
- Left/Right: 1.5rem - 2rem
- Top/Bottom (sections): 1.5rem
```

---

## ESTADO VACÍO vs ESTADO CON ACTIVIDAD

### ESTADO VACÍO (primer uso / sin historial)

```
HEADER
Portable Work Router | Retoma tu trabajo...

CONTINUAR TRABAJO RECIENTE
┌─────────────────────────────────────────────┐
│ Todavía no hay tareas ejecutadas            │
│                                             │
│ [Capturar primera tarea →]                  │
│                                             │
│ Comienza capturando una tarea para retomar  │
│ el trabajo cuando regreses                  │
└─────────────────────────────────────────────┘

CAPTURA RÁPIDA
┌─────────────────────────────────────────────┐
│ + Pensar, escribir, programar...            │
│ ⚙️ Opciones   📎 Archivos   🏢 Proyecto    │
│ [Capturar]                                  │
└─────────────────────────────────────────────┘

PROYECTOS RECIENTES
┌─────────────────────────────────────────────┐
│ Todavía no hay proyectos                    │
│                                             │
│ [Crear primer proyecto →]                   │
└─────────────────────────────────────────────┘

CREAR PROYECTO
(ya visible arriba, no aparece botón duplicado)
```

### ESTADO CON ACTIVIDAD (con historial)

```
HEADER
Portable Work Router | Retoma tu trabajo...

CONTINUAR TRABAJO RECIENTE
┌─────────────────────────────────────────────┐
│ 📋 Explicar algoritmo de búsqueda [ACTIVO]  │
│ PWR · Pensar · ECO · Hace 1 hora            │
│ [Continuar]                                 │
├─────────────────────────────────────────────┤
│ 📋 Documentar endpoints API                  │
│ PWR · Escribir · ECO · Ayer                 │
│ [Continuar]                                 │
├─────────────────────────────────────────────┤
│ 📋 Revisar PR #284                          │
│ PWR · Revisar · Sonnet · Lunes              │
│ [Continuar]                                 │
└─────────────────────────────────────────────┘

CAPTURA RÁPIDA
┌─────────────────────────────────────────────┐
│ + Pensar, escribir, programar...            │
│ ⚙️ Opciones   📎 Archivos   🏢 Proyecto    │
│ [Capturar]                                  │
└─────────────────────────────────────────────┘

PROYECTOS RECIENTES
┌─────────────────────┐ ┌─────────────────────┐
│ 📁 PWR              │ │ 📁 RosmarOps        │
│ 3 tareas activas    │ │ 5 tareas activas    │
│ Última: hace 1 hora │ │ Última: ayer        │
│ [Abrir]        ⭐   │ │ [Abrir]        ⭐   │
└─────────────────────┘ └─────────────────────┘
[Ver todos →]

CREAR PROYECTO
[+ Crear nuevo proyecto]
```

---

## RESPUESTA A "¿QUÉ HAGO AHORA AQUÍ?" en 3 SEGUNDOS

```
VISTA INMEDIATA (sin scroll):
1. Header pequeño explica qué es PWR
2. CONTINUAR RECIENTE → usuario ve su última tarea y botón [Continuar]
3. CAPTURA RÁPIDA → si no continúa, puede capturar nueva tarea
4. PROYECTOS RECIENTES → contexto de dónde estaba

RESPUESTA: "Puedo continuar trabajando en mi última tarea,
o capturar una nueva, o cambiar de proyecto"
```

---

## VISUAL WEIGHT HIERARCHY

```
1. CONTINUAR TRABAJO (80% del enfoque)
   - Más grande, mejor destacado, botón principal visible

2. CAPTURA RÁPIDA (70% del enfoque)
   - Input limpio, accesible, claro

3. PROYECTOS RECIENTES (60% del enfoque)
   - Informativo, contexto de dónde estaba

4. CREAR PROYECTO (30% del enfoque)
   - Pequeño, outline, secundario

HEADER (40% del enfoque)
   - Compacto, contextual, NO distrae
```

---

## CAMBIOS vs ACTUAL

| Aspecto | Actual | Nuevo |
|---------|--------|-------|
| Header | 140px + métricas | 70px compacto |
| Protagonista | Buscar proyecto | Continuar reciente |
| Entrada | En "crear proyecto" modal | Visible top (CAPTURA) |
| Proyectos | Lista plana con botones | Tarjetas con info context |
| Crear proyecto | Botón principal destacado | Botón secundario discreto |
| Aire muerto | Mucho | Mínimo, bloques con entidad |
| Respuesta 3s | "Gestiono proyectos" | "Retomo mi trabajo" |

---

**Este wireframe responde**:
- ✅ Retomar trabajo (CONTINUAR es protagonista)
- ✅ Captura visible (segundo bloque, no modal)
- ✅ Proyectos como contexto (tercer bloque)
- ✅ Crear como secundaria (botón pequeño abajo)
- ✅ Aire muerto eliminado (bloques densos, información útil)
- ✅ Header reducido (70px vs 140px)
- ✅ Presentación con entidad (tarjetas, no lista plana)
- ✅ Responde en 3 segundos (flujo obvio: continuar → capturar → proyecto)

**¿Validado? Una vez confirmes este wireframe, paso a la implementación visual en HTML + código.**
