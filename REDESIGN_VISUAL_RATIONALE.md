# Rediseño Visual - Propuesta B2B Seria

**Propuesta de UI ambiciosa y concreta** para PWR v1 final
Enfoque: Calidad percibida, peso visual, continuidad de trabajo

---

## El Problema Con La Versión Anterior

### Síntomas
- **Aire muerto**: Espacios amplios pero vacíos de significado
- **Jerarquía débil**: Router Decision, Resultado y Captura compiten sin ganador claro
- **Sidebar como formulario**: Parece un panel de configuración, no un centro de trabajo
- **Centro demasiado vacío**: Estado inicial no comunica qué hacer
- **Controles sin presencia**: Botones y acciones no tienen peso visual
- **Falta de flujo**: No se siente como una herramienta para trabajar en serio

### Raíz del problema
Éramos demasiado literales con wireframes. Seguimos la estructura sin pensar en **sensación de uso**, **continuidad de contexto**, y **peso visual profesional**.

---

## Estrategia Del Nuevo Diseño

### 1. Header Reducido (No Protagonista)
**Antes**: Header grande con título y proyectos
**Ahora**: Breadcrumb integrado + nombre proyecto + botón cerrar

```
┌────────────────────────────────────────┐
│ Proyecto > Portable Work Router [close] │  ← Compacto, contextual
└────────────────────────────────────────┘
```

**Efecto**: El proyecto es contexto, no el centro de atención. La pantalla NO es sobre el proyecto, es sobre el TRABAJO dentro del proyecto.

---

### 2. Sidebar: De "Ficha" a "Centro de Control"

#### Cambios Estructurales

**Antes**:
```
- Proyecto resumido (panel)
- Captura compacta (expandible)
- Lista de tareas (abajo)
```

**Ahora**:
```
CONTEXT BAR (siempre visible)
├─ Objetivo, Docs, Tags
├─ Compacto: 3-4 líneas máximo

COMMAND BAR (acción inmediata)
├─ Input de captura
├─ Ícono + placeholder descriptivo
├─ Acceso directo, sin expandible

TASK LIST (protagonista)
├─ Listado permanente
├─ Filtrado por estado
├─ Estados visuales claros
```

#### Rationale

**Context Bar** (reducido):
- Proyecto no necesita ficha completa visible
- Solo lo esencial: ¿tiene objetivo? ¿tiene docs? ¿tiene reglas?
- Ocupación: 4-5 líneas máximo
- Función: Recordar contexto sin ocupar espacio

**Command Bar** (nunca colapsado):
- La captura es el MOTOR de la herramienta
- Debe estar siempre visible y accesible
- Input con ícono (⚡) sugiere "crear tareas rápido"
- Placeholder descriptivo: "¿Qué necesitas? (Pensar, Escribir, Programar...)"
- **No expandible**: opciones mostradas solo cuando se ejecuta o en modal

**Task List** (ahora con presencia):
- Ocupa espacio de verdad
- Items visibles sin scroll si es posible
- Estados visuales: active (blue left border), hover (light bg)
- Meta información clara: tipo, modelo, timestamp
- Entrada directa: click en tarea abre en main

### 3. Main Area: Router Decision = Gateway a Trabajo

#### Estructura

```
ROUTER PANEL (siempre primer elemento visible)
├─ Modo ECO/RACING (badge color + descriptor)
├─ Razón (párrafo legible, no lista)
├─ Métricas grid (2x2: Modelo, Proveedor, Latencia, Coste)
└─ Acciones: [Ejecutar] [Cambiar a RACING]

[Espacio]

RESULTADO (vacío o lleno, siempre segundo)
├─ STATE VACÍO: Guidance + 3 pasos
├─ STATE LLENO: Contenido + extracto + acciones
```

#### Cambios Clave

**Router Panel**:
- `border-left: 4px solid #10B981` (eco) / `#F59E0B` (racing)
- Razón es párrafo legible, no lista de razones
- Métricas en grid 2x2 (compacto pero legible)
- Botones de acción al pie (Ejecutar, Cambiar modo)
- **Efecto visual**: Panel con "peso", no wireframe

**Resultado - Estado Vacío**:
```
📝 Resultado pendiente

Ejecuta el Router para ver el análisis y salida de la tarea.

1️⃣ Configura el tipo y contexto si lo necesitas
2️⃣ Haz clic en "Ejecutar" arriba
3️⃣ El resultado aparecerá aquí listo para editar
```

- Guía el usuario sin ser condescendiente
- Usa números para claridad
- Comunica: "esto es el espacio donde ocurre el trabajo"

**Resultado - Con Contenido**:
```
RESULTADO [header muted]

[Contenido principal, scrollable]

[Extracto en box destacado, morado]

[Botones de acción: Guardar, Crear activo, Editar]
```

- Contenido editable, no solo visualización
- Extracto visualmente destacado (left border morado)
- Acciones claras y disponibles

---

## Detalles Visuales de Calidad

### Espaciado Consciente
- **Header**: 0.75rem padding (compacto, respeta contenido)
- **Sidebar top**: 1rem (respira un poco)
- **Command bar**: 0.75rem (accesible pero integrado)
- **Main content**: 1.5rem (espacio de trabajo, "respiración")
- **Gaps**: 1.5rem entre paneles (separa pero no fragmenta)

### Color y Peso
- **Fondos**: White (#FFFFFF) en paneles, Light gray (#FAFBFC) en workspace
- **Bordes**: Subtle (#E2E8F0) para separación, NO lineas fuertes
- **Accent**: Verde para ECO (#10B981), Ámbar para RACING (#F59E0B)
- **Texto**: Jerarquía clara pero sobria (no colorines)

### Estados Visuales
- **Task item hover**: Fondo light, NO cambio de color
- **Task item active**: Left border azul (2px), fondo light blue
- **Button hover**: Cambio sutil de fondo
- **Input focus**: Muy light shadow, NO outline

### Tipografía
- **Header proyecto**: 13px bold uppercase (contexto)
- **Task title**: 13px bold regular
- **Body text**: 13px regular (legible)
- **Meta**: 11px muted (secundario)
- **Labels**: 11px bold uppercase + 0.5px letter-spacing

---

## Flujo de Usuario (Mejorado)

### Estado Inicial
1. Abre proyecto → Ve header + contexto bar + comando bar + lista de tareas
2. Ve router panel con decisión recomendada (si es primera vez, está vacío pero con guía)
3. Ve espacio de resultado con "estado pendiente" y pasos

### Flujo Natural
1. **Opción A**: Escribir en command bar → Click crear → Aparece en lista → Click en lista → Se abre en main → Click ejecutar → Resultado aparece
2. **Opción B**: Click en tarea existente en lista → Se abre en main → Click ejecutar → Resultado aparece
3. **Continuar**: Editar resultado → Guardar o crear activo

**Vs antes**: El flujo es más claro. No hay expandibles ni UI sorpresa. Todo está donde se espera.

---

## Qué Se Mantiene de Fases 1-4

✅ Layout master-detail (sidebar + main)
✅ Router decision prominent
✅ Resultado como segundo panel
✅ Task list functional
✅ Styling coherente

## Qué Cambia

✅ Header reducido y menos prominente
✅ Sidebar ahora es "control center", no "project sheet"
✅ Captura como command bar, siempre visible
✅ Task list con presencia visual
✅ Router panel con mejor jerarquía visual
✅ Resultado con estado vacío útil
✅ Espaciado y peso visual mejorados
✅ Sin expandibles innecesarios (modal para opciones después)

---

## Próxima Fase: Implementación

Una vez validada esta propuesta visual:

1. **Refactor app.py** con nuevo layout y CSS mejorado
2. **Eliminar**: Header grande, sidebar form, expandibles
3. **Añadir**: Context bar, command bar como inline, mejor task list styling
4. **Mejorar**: CSS injection para espaciado, bordes, colores
5. **Testing**: Verificar que se siente como herramienta seria, no wireframe

---

**Estado**: ✅ Propuesta visual lista en `PWR_VISUAL_PROPOSAL.html`

Abre el archivo en navegador para ver ambos estados:
1. Resultado vacío (con guidance)
2. Resultado lleno (con contenido)

¿Validación de dirección visual?
