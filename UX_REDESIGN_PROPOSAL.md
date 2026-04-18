# Propuesta de Rediseño UX/UI - PWR Router v1

**Fase 1: Análisis + Propuesta Estructural (sin código)**

---

## PARTE 1: DIAGNÓSTICO DE LA UX ACTUAL

### 1.1 Estado actual: Por qué parece un formulario

**La estructura actual (app.py):**

```
Sidebar (izquierda)
  ├─ Título + descripción
  ├─ Selector de proyecto
  └─ Tagline

Main area (derecha)
  ├─ Home view (si no hay proyecto)
  │  └─ "Crear Proyecto" (botón central)
  │
  └─ Project view (si hay proyecto)
     ├─ Header con nombre del proyecto
     ├─ Dos columnas: LEFT / RIGHT
     │  │
     │  ├─ LEFT
     │  │  ├─ "Captura rápida" (bloque)
     │  │  │  ├─ Título (input)
     │  │  │  ├─ Tipo de trabajo (selectbox)
     │  │  │  ├─ ¿Qué necesitas hacer? (textarea)
     │  │  │  ├─ Contexto específico (textarea)
     │  │  │  ├─ Adjuntos (file uploader)
     │  │  │  └─ "Crear tarea" (botón)
     │  │  │
     │  │  ├─ "Tareas" (bloque)
     │  │  │  ├─ Búsqueda
     │  │  │  └─ Lista de tareas (inline)
     │  │  │
     │  │  └─ "Activos recientes" (bloque)
     │  │
     │  └─ RIGHT
     │     ├─ (si no seleccionó tarea)
     │     │  └─ "Selecciona una tarea"
     │     │
     │     └─ (si seleccionó tarea)
     │        ├─ Título + descripción (display)
     │        ├─ "Decisión de modelo" (caja)
     │        ├─ "Prompt sugerido" (code block)
     │        ├─ "Ver trazabilidad" (expander)
     │        ├─ "Resultado" (dos textareas grandes)
     │        │  ├─ Pega aquí el resultado...
     │        │  └─ Extracto reusable...
     │        ├─ Botones (Guardar, Crear activo)
     │        └─ "Activos recientes del proyecto" (bloque)
```

### 1.2 Problemas de UX identificados

#### Problema 1: Jerarquía visual invertida

**Hoy:**
- La captura ocupa la mitad izquierda, pero es un "input area"
- El resultado, que es lo valioso, está en un bloque genérico más abajo a la derecha
- La lista de tareas es un addon secundario
- El Router (decisión del sistema) está escondido en un expander

**Sensación:** "Rellena campos, luego mira qué pasó"

**Debería ser:** "Mira el resultado, mira la decisión, luego ajusta si quieres"

---

#### Problema 2: Captura como formulario de alta

**Hoy:**
```
├─ Título (text input)
├─ Tipo de trabajo (selectbox 5 opciones iguales)
├─ ¿Qué necesitas hacer? (textarea grande)
├─ Contexto específico (textarea grande)
├─ Adjuntos (file uploader)
└─ [Crear tarea]
```

**El problema:**
- 5 campos visibles en paralelo
- Todos parecen igual de importantes
- La entrada principal ("qué necesitas") aparece tercero
- Sensación: "debo llenar un formulario antes de que pase nada"

**Debería ser:**
```
┌─ ¿Qué necesitas hacer? [input rápido] [crear]
├─ Tipo: [selectbox compacto]
├─ Contexto: [expandible bajo demanda]
└─ Adjuntos: [expandible bajo demanda]
```

**Sensación:** "digo qué necesito, y luego refinó si quiero"

---

#### Problema 3: Falta de navegación clara

**Hoy:**
- No hay "breadcrumb" o contexto de dónde estoy
- El selector de proyecto en sidebar es la única orientación
- Si el usuario está perdido, no hay "volver atrás"
- No hay indicación visual de: Home → Proyecto → Tarea

**Debería ser:**
- Breadcrumb claro: Home > Mi Proyecto > Tarea X
- Back button si es necesario
- Indicador visual de "aquí estoy"

---

#### Problema 4: Router no es creíble

**Hoy:**
- "Decisión de modelo" está en un box pequeño debajo de la tarea
- El Router summary es texto plano
- La trazabilidad está en un expander (escondida)
- No hay confianza visual en que el sistema realmente decide

**Debería ser:**
- Router visible como un panel central
- Decisión clara: "ECO porque [razón]"
- Latencia, costo, modelo visibles de un vistazo
- Trazabilidad accesible pero no invasiva

---

#### Problema 5: Overload de información en un único scroll

**Hoy:**
- En pantalla de proyecto (columna derecha), hay:
  - Título tarea
  - Decisión modelo
  - Prompt sugerido
  - Trazabilidad (expander)
  - Resultado (2 textareas)
  - Botones
  - Activos recientes
- Todo vertical, todo en un scroll
- Es difícil saber "qué es lo importante aquí"

**Debería ser:**
- Zoom en la tarea activa
- Resultado como protagonista
- Decisión del Router visible pero no invasiva
- Contexto secundario bajo demanda

---

#### Problema 6: Activos aparecen al final

**Hoy:**
- Activos recientes están al final del scroll derecho
- Misma importancia visual que el prompt
- El usuario puede crear un activo pero no siente que es la meta del flujo

**Debería ser:**
- Conversión de resultado → activo como flujo natural
- Activos como galería clara, no como lista de texto

---

#### Problema 7: Proyecto context es invasivo

**Hoy:**
- Hay una "Ficha del proyecto" que expande y ocupa media pantalla
- Es editable inline (demasiado poder)
- Distrae del trabajo real

**Debería ser:**
- Contexto del proyecto visible pero resumido
- Editable en un modal, no inline

---

### 1.3 Por qué transmite "formulario de Google Forms desordenado"

**Razones principales:**

1. **Estructura vertical homogénea**
   - Todo son "cajas" con título y contenido
   - No hay jerarquía visual clara
   - Parece un form builder genérico

2. **Énfasis en entrada, no en salida**
   - El 40% de la pantalla es "captura"
   - El resultado está abajo
   - Las decisiones del sistema están escondidas

3. **Falta de espacios negativos**
   - Todo está abarrotado
   - No hay "respiración" visual
   - Sensación de densidad sin intención

4. **Botones compitiendo**
   - Demasiados botones de igual peso
   - No está claro "qué debería hacer ahora"
   - Sensación caótica

5. **Sidebar no transmite "workspace"**
   - El sidebar es solo navegación
   - No tiene herramientas de contexto
   - No se siente como "mi espacio de trabajo"

---

### 1.4 Flujo de uso actual vs ideado

**Hoy (problemático):**
```
1. Llega a home
   → "Crear Proyecto" (botón único, toma 5 segundos)

2. Entra a proyecto
   → Panel izquierdo: rellenar campos (5 inputs iguales)
   → "Crear tarea"

3. Tarea creada
   → Mira resultado en panel derecho (abajo, bajo scroll)
   → "¿Qué decidió el sistema?" (expander escondido)
   → "Guardar resultado"
   → "Crear activo"

Sensación: "formulario" → "esperar resultado" → "acciones al final"
```

**Ideado (productivo):**
```
1. Llega a home
   → Proyectos recientes destacados
   → "Abrir proyecto" o "Crear nuevo"

2. Entra a proyecto (pantalla de workspace)
   → Lista de tareas claras a la izquierda
   → Tarea activa en el centro
   → Decisión del Router visible arriba

3. Selecciona tarea
   → Resultado en protagonista
   → Router decision clara
   → Botones de acción en jerarquía: [Ejecutar] [Guardar] [Crear activo]

Sensación: "workspace" → "selecciono trabajo" → "veo resultado" → "actúo"
```

---

## PARTE 2: NUEVO LAYOUT ESTRUCTURAL

### 2.1 Home Redesigned

**Actual:**
```
┌─────────────────────────────────┐
│ [Selector de proyecto en sidebar]
│ ┌─ Crear Proyecto               │
│ │                               │
│ └─────────────────────────────┘
```

**Propuesto:**
```
┌─────────────────────────────────────────────────────────┐
│  PORTABLE WORK ROUTER                                   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Proyectos recientes                            │   │
│  │  ┌──────────────  ┌──────────────  ┌─────────┐ │   │
│  │  │ Mi Proyecto 1  │ RosmarOps      │ +Nuevo  │ │   │
│  │  │ 3 tareas       │ 5 tareas       │ Proyecto│ │   │
│  │  │ [abrir]        │ [abrir]        │         │ │   │
│  │  └────────────────┴────────────────┴─────────┘ │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Buscar proyecto                                │   │
│  │  [────────────────────────────────────]         │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Últimas tareas ejecutadas                      │   │
│  │  • Tarea 1 - en Mi Proyecto 1 - hace 2h        │   │
│  │  • Tarea 2 - en RosmarOps - hoy                │   │
│  │  • Tarea 3 - en Mi Proyecto 1 - ayer          │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

**Cambios:**
- No "crear proyecto" como acción principal
- Proyectos recientes como tarjetas (no lista)
- Busca de proyecto visible
- Últimas tareas ejecutadas como contexto

---

### 2.2 Pantalla de Proyecto - Master-Detail Layout

**Actual (vertical, homogéneo):**
```
┌──────────┬───────────────────────┐
│ Sidebar  │ Panel derecho (scroll) │
│          │ todo mezclado         │
│          │ input + output        │
│          │ vertically stacked    │
└──────────┴───────────────────────┘
```

**Propuesto (workspace serio):**
```
┌─────────────────────────────────────────────────────────────┐
│ Home > Mi Proyecto                                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌──────────────────┬─────────────────────────────────────┐ │
│ │ NAVEGACIÓN       │ ZONA DE TRABAJO                     │ │
│ │ IZQUIERDA        │ CENTRAL / DERECHA                   │ │
│ │                  │                                     │ │
│ │ [Contexto        │ ┌─────────────────────────────────┐ │ │
│ │  Proyecto]       │ │ ROUTER DECISION                 │ │ │
│ │                  │ │ ┌─────────────────────────────┐ │ │ │
│ │ [Captura         │ │ │ ECO                         │ │ │ │
│ │  Rápida]         │ │ │ Razón: complejidad baja     │ │ │ │
│ │                  │ │ │ Modelo: 2.5-flash-lite     │ │ │ │
│ │ [Lista de        │ │ │ Latencia: 234ms             │ │ │ │
│ │  Tareas]         │ │ │ Coste: $0.05                │ │ │ │
│ │  • Tarea 1       │ │ │ [Ver detalles ▼]            │ │ │ │
│ │  • Tarea 2 ◄───→ │ │ └─────────────────────────────┘ │ │ │
│ │  • Tarea 3       │ │                                 │ │ │
│ │                  │ │ ┌─────────────────────────────┐ │ │ │
│ │                  │ │ │ RESULTADO                   │ │ │ │
│ │                  │ │ │ [Output real de Gemini]     │ │ │ │
│ │                  │ │ │                             │ │ │ │
│ │                  │ │ │ Lorem ipsum dolor sit amet  │ │ │ │
│ │                  │ │ │ consectetur adipiscing...   │ │ │ │
│ │                  │ │ │                             │ │ │ │
│ │                  │ │ └─────────────────────────────┘ │ │ │
│ │                  │ │                                 │ │ │
│ │                  │ │ ┌─────────────────────────────┐ │ │ │
│ │                  │ │ │ [Extracto reusable]         │ │ │ │
│ │                  │ │ │ [Guardar] [Crear activo]    │ │ │ │
│ │                  │ │ └─────────────────────────────┘ │ │ │
│ │                  │ │                                 │ │ │
│ │                  │ │ [Ficha del proyecto ▼]          │ │ │
│ │                  │ │ [Prompt sugerido ▼]             │ │ │
│ │                  │ │ [Trazabilidad ▼]                │ │ │
│ │                  │ │ [Activos relacionados ▼]        │ │ │
│ │                  │                                     │ │ │
│ │                  │ [Ejecutar con Router] [Duplicar]   │ │ │
│ └──────────────────┴─────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Cambios clave:**

1. **Sidebar izquierdo:**
   - Contexto del proyecto (resumido, siempre visible)
   - Captura rápida (compacta, en la parte superior)
   - Lista de tareas (clara, con búsqueda)

2. **Centro-derecha (zona de trabajo):**
   - **Panel superior:** Router decision (visible, creíble, compacto)
   - **Panel central:** Resultado (protagonista, grande)
   - **Panel secundario:** Extracto reusable + botones
   - **Expandibles bajo demanda:** Ficha, Prompt, Trazabilidad, Activos

3. **Jerarquía de botones:**
   - Principal: `[Ejecutar con Router]`
   - Secundaria: `[Guardar] [Crear activo] [Duplicar]`
   - Raramente accesible: edición de proyecto

---

### 2.3 Zona de Captura Redesigned

**Actual (5 campos visibles):**
```
Captura rápida
├─ Título (input)
├─ Tipo de trabajo (selectbox)
├─ ¿Qué necesitas hacer? (textarea)
├─ Contexto específico (textarea)
├─ Adjuntos (uploader)
└─ [Crear tarea]
```

**Propuesto (entrada progresiva):**
```
┌─────────────────────────────────┐
│ Captura rápida                  │
│                                 │
│ ┌─────────────────────────────┐ │
│ │ ¿Qué necesitas hacer?       │ │
│ │ [input rápido] [crear]      │ │
│ └─────────────────────────────┘ │
│                                 │
│ ▼ Opciones (expandible)         │
│ ├─ Tipo: [selectbox compacto]  │
│ ├─ Contexto: [textarea pequeño]│
│ └─ Archivos: [upload]          │
│                                 │
└─────────────────────────────────┘
```

**Cambios:**
- Pregunta principal bien visible
- Opciones bajo demanda
- Botón "crear" al lado del input (no abajo)
- Sensación: "digo qué necesito y listo"

---

### 2.4 Zona de Router Decision

**Actual (caja pequeña, secundaria):**
```
Decisión de modelo
│ Modelo recomendado: gemini-2.5-flash-lite
│ Modo: eco
│ Nivel de complejidad: 0.25
│ [Ver trazabilidad ▼]
```

**Propuesto (panel central, creíble):**
```
┌──────────────────────────────────┐
│ ROUTER DECISION                  │
├──────────────────────────────────┤
│                                  │
│  ECO                             │
│  ▲                               │
│  │ rápido + barato               │
│                                  │
│  Razón:                          │
│  Complejidad baja, tarea simple. │
│  Priorizar velocidad.            │
│                                  │
│  Modelo: gemini-2.5-flash-lite  │
│  Latencia: 234ms | Coste: $0.05 │
│                                  │
│  [Cambiar a RACING]              │
│  [Ver detalles ▼]                │
│                                  │
└──────────────────────────────────┘
```

**Cambios:**
- Visible sin scroll
- Modo en grande (ECO / RACING)
- Razón humana legible
- Opción de cambiar modo manualmente
- Métricas claras

---

### 2.5 Zona de Resultado

**Actual (textarea genérica):**
```
Resultado
┌────────────────────────────────┐
│ Pega aquí el resultado del     │
│ modelo o revisa el generado    │
│ por el Router                  │
│ [output del modelo aquí]       │
└────────────────────────────────┘

Extracto reusable
┌────────────────────────────────┐
│ [primeros 700 chars]           │
└────────────────────────────────┘
```

**Propuesto (panel protagonista):**
```
┌────────────────────────────────────┐
│ RESULTADO                          │
├────────────────────────────────────┤
│                                    │
│ [output del modelo, bien visible]  │
│                                    │
│ Lorem ipsum dolor sit amet...      │
│ consectetur adipiscing elit...     │
│ sed do eiusmod tempor...           │
│                                    │
│ ┌────────────────────────────────┐ │
│ │ Extracto reutilizable          │ │
│ │ [resumen o extracto]           │ │
│ └────────────────────────────────┘ │
│                                    │
│ [Guardar] [Crear activo]          │
│ [Editar] [Duplicar]                │
│                                    │
└────────────────────────────────────┘
```

**Cambios:**
- Resultado como protagonista
- Extracto integrado, no separado
- Botones de acción claros
- Mejor legibilidad

---

### 2.6 Lista de Tareas

**Actual (inline, lista simple):**
```
Tareas
[búsqueda]
• Tarea 1
• Tarea 2
• Tarea 3
```

**Propuesto (con estado visual claro):**
```
┌──────────────────────────┐
│ TAREAS (3)               │
├──────────────────────────┤
│ [búsqueda]               │
│                          │
│ ▪ Tarea 1                │
│   pendiente | hace 2h    │
│                          │
│ ▪ Tarea 2 ◄ (activa)    │
│   completada | hace 1h   │
│   [ejecutar de nuevo]    │
│                          │
│ ▪ Tarea 3                │
│   completada | ayer      │
│                          │
│ [+Nueva tarea]           │
└──────────────────────────┘
```

**Cambios:**
- Estado visible (pendiente, completada)
- Timestamp
- Indicador de cuál es activa
- Acciones rápidas por tarea

---

### 2.7 Sidebar izquierdo: Ficha del Proyecto

**Actual (expander que ocupa media pantalla):**
```
▼ Ficha del proyecto
Objetivo:
[textarea grande con contenido]

Contexto de referencia:
[textarea grande con contenido]

Reglas estables:
[textarea grande con contenido]

[Guardar cambios] [Cancelar edición]
```

**Propuesto (siempre resumido):**
```
┌──────────────────────────┐
│ PROYECTO                 │
├──────────────────────────┤
│ Mi Proyecto              │
│ 3 tareas | 2 activos     │
│                          │
│ Objetivo:                │
│ Organizar trabajo con... │
│ [editar ▼]               │
│                          │
│ Contexto: Sí             │
│ Reglas: Sí               │
│                          │
└──────────────────────────┘
```

**Cambios:**
- Resumido por defecto
- "Editar" abre un modal, no expande inline
- Indicadores: "Contexto: Sí", "Reglas: Sí"
- No invade el workspace

---

### 2.8 Expandibles: Ficha Completa, Prompt, Trazabilidad

**Propuesto (bajo demanda):**
```
┌─────────────────────────────────────┐
│ [▼ Ficha del proyecto (editar)]      │
│ ┌─────────────────────────────────┐ │
│ │ Objetivo:                       │ │
│ │ [textarea]                      │ │
│ │                                 │ │
│ │ Contexto:                       │ │
│ │ [textarea]                      │ │
│ │                                 │ │
│ │ Reglas:                         │ │
│ │ [textarea]                      │ │
│ │                                 │ │
│ │ [Guardar] [Cancelar]            │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ [▼ Prompt sugerido]                 │
│ ┌─────────────────────────────────┐ │
│ │ PROYECTO                        │ │
│ │ Mi Proyecto                     │ │
│ │                                 │ │
│ │ TAREA                           │ │
│ │ Explicar recursión              │ │
│ │ ...                             │ │
│ │                                 │ │
│ │ [Copiar] [Usar como base]       │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ [▼ Trazabilidad]                    │
│ ┌─────────────────────────────────┐ │
│ │ Estado: COMPLETED               │ │
│ │ Modo: eco                       │ │
│ │ Modelo: gemini-2.5-flash-lite  │ │
│ │ Proveedor: gemini               │ │
│ │ Latencia: 234 ms                │ │
│ │ Coste estimado: $0.05           │ │
│ │                                 │ │
│ │ Motivo de decisión:             │ │
│ │ Complejidad baja...             │ │
│ │                                 │ │
│ │ [Copiar trace] [Exportar]       │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

---

## PARTE 3: JERARQUÍA DE INTERACCIÓN

### 3.1 En Home

**Acciones principales (bien visibles):**
1. Click en proyecto reciente → Abrir workspace
2. Crear nuevo proyecto → Abrir modal

**Acciones secundarias (bajo demanda):**
- Buscar proyecto
- Ver últimas tareas

---

### 3.2 En Project View - Zona Izquierda (Navegación)

**Acciones principales:**
1. Click en tarea → Cargar en zona central
2. Escribir en "¿Qué necesitas?" + [crear] → Nueva tarea

**Acciones secundarias:**
- Búsqueda de tareas
- Expandir ficha del proyecto
- Editar proyecto (modal)

**Siempre visible:**
- Lista de tareas
- Contexto resumido del proyecto

---

### 3.3 En Project View - Zona Central (Trabajo)

**Acciones principales:**
1. `[Ejecutar con Router]` → Ejecutar tarea con Gemini
2. `[Crear activo]` → Guardar resultado como activo reutilizable

**Acciones secundarias:**
1. `[Guardar]` → Guardar edición del resultado
2. `[Cambiar a RACING]` → Cambiar modo manualmente
3. Ver detalles de trazabilidad (expandible)

**Siempre visible (sin scroll):**
- Router decision (panel compacto)
- Resultado (protagonista)

**Bajo demanda (expandibles):**
- Ficha del proyecto (edición)
- Prompt sugerido
- Trazabilidad completa
- Activos relacionados

---

### 3.4 Estado visual por pantalla

**Home:**
```
- Proyectos recientes: ★★★ importante
- Crear nuevo: ★★ secundario
- Buscar: ★ accesorio
```

**Project View:**
```
- Router decision: ★★★ importante
- Resultado: ★★★ importante
- [Ejecutar]: ★★★ botón principal
- Tareas (sidebar): ★★★ navegación
- Captura: ★★ creación de trabajo
- Expandibles: ★ bajo demanda
```

---

## PARTE 4: CAMBIOS MÍNIMOS vs ESTRUCTURALES

### 4.1 Sin tocar backend (arquitectura preservada)

**Se mantiene intacto:**
- Modelo de datos (projects, tasks, assets)
- SQLite + persistencia
- Router v1
- Decisión eco/racing
- ExecutionService
- White box / trazabilidad
- Persistencia de resultados

**Cambios en app.py (solo presentación):**
- Reorganizar Streamlit layout
- Cambiar estructura de columnas
- Mover expandibles
- Redefinir orden visual
- Agregar breadcrumb / contexto
- Cambiar CSS (inyectado)

### 4.2 Pequeños cambios necesarios en app.py

1. **Home view (actual muy simple, mejorar):**
   - Agregar proyectos recientes como tarjetas
   - Agregar busca
   - Agregar últimas tareas

2. **Project view (reorganizar):**
   - Cambiar layout de 2 columnas a sidebar + main
   - Reordenar bloques: Router primero, resultado segundo
   - Compactar captura
   - Expandibles para: Ficha, Prompt, Trazabilidad, Activos

3. **Breadcrumb (agregar):**
   - "Home > Mi Proyecto > Tarea X"
   - Navegación visual

4. **CSS (mejorar):**
   - Jerarquía visual clara
   - Espacios negativos
   - Tipografía sobria
   - Colores B2B (sin emojis)

### 4.3 Qué NO tocar

- Lógica de decisión del Router
- Persistencia de tareas
- Conversión a activos
- Ejecución con Gemini
- Cálculo de complejidad
- Generación de prompts

---

## PARTE 5: ESTRATEGIA DE IMPLEMENTACIÓN

### 5.1 Orden de cambios (sin romper lo funcional)

**Fase 1: Estructura base (1-2 horas)**
1. Cambiar layout principal a sidebar + main
2. Mover elementos en orden correcto
3. Verificar que sigue funcionando

**Fase 2: Home mejorado (1 hora)**
1. Agregar tarjetas de proyectos recientes
2. Agregar busca
3. Agregar últimas tareas

**Fase 3: Jerarquía en Project View (2-3 horas)**
1. Compactar captura
2. Router decision visible arriba
3. Resultado como protagonista
4. Expandibles para otros

**Fase 4: Pulido visual (1-2 horas)**
1. Breadcrumb
2. CSS mejorado
3. Tipografía
4. Espacios

**Fase 5: Validación (1 hora)**
1. Test de flujos
2. Verificar persistencia
3. Verificar Router funciona

---

### 5.2 Mapa de cambios por archivo

**app.py:**
- Función `home_view()`: Rediseñar completamente (mostrar proyectos recientes)
- Función `project_view()`: Reorganizar layout (sidebar + main)
- Función `project_selector()`: Mantener o mejorar ligeramente
- CSS en `inject_css()`: Mejorar jerarquía visual
- Agregar breadcrumb (función nueva)
- Expandibles (expanders reordenados)

**No tocar:**
- `router/` (intacto)
- BD schema
- Funciones de negocio (create_task, create_asset, etc.)

---

### 5.3 Preservación de funcionalidad

**Checklist de conservación:**

- [ ] Crear proyecto sigue funcionando
- [ ] Crear tarea sigue funcionando
- [ ] Ejecutar con Router sigue funcionando
- [ ] Guardar resultado sigue funcionando
- [ ] Crear activo sigue funcionando
- [ ] Datos se persisten en SQLite
- [ ] Router decide eco/racing correctamente
- [ ] White box muestra información correcta

---

## RESUMEN EJECUTIVO: EL CAMBIO

### De:
```
formulario de captura → resultado perdido abajo → Router escondido
```

### A:
```
workspace profesional → resultado visible → decisión del Router clara
```

### La transformación es:
- **Estructural**, no cosmética (reorganizar zonas)
- **Preservadora**, no destructiva (backend intacto)
- **Progresiva**, no de golpe (por fases)
- **Mínima**, en líneas de código (solo layout)
- **Máxima**, en impacto visual (sensación de producto)

---

**Siguiente paso:** Una vez validada esta propuesta, pasamos a la implementación detallada archivo por archivo.

¿Validás esta dirección de rediseño?
