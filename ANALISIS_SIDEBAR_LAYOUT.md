# ANÁLISIS: Sidebar vs Espacio Útil en Flujos

## Observación inicial

La sidebar no solo añade ruido visual: **roba espacio horizontal crítico** que afecta la legibilidad del flujo principal en estados como onboarding y nueva tarea.

---

## 1. CUÁNTO ESPACIO ÚTIL PIERDO HOY POR LA SIDEBAR

### Layout actual de Streamlit

```
┌─────────────────────────────────────────────────────────────────────┐
│ SIDEBAR (25-30%)  │  MAIN CONTENT (70-75%)                         │
│ ·PWR              │                                                 │
│ ·🏠 Home          │  ¿Cuál es tu tarea?                           │
│ ·📡 Radar         │  [Input]                                       │
│ ·──────            │  [Preview]                                     │
│ ·📁 Proyecto      │  [Botón]                                       │
│ ·📌 Tarea        │                                                 │
└─────────────────────────────────────────────────────────────────────┘

Desktop típico: ~1440px ancho
Sidebar: ~360px (25%)
Main: ~1080px (75%)

Pero en realidad:
Sidebar útil para flujo: ~5% del espacio
Sidebar útil para navegación: ~20% del espacio
```

### Distribución de contenido por estado

#### ESTADO A: Onboarding
```
Contenido principal necesario:
  - Pregunta: "¿Cuál es tu tarea?" (50px)
  - Input: 120px
  - Ejemplos: 40px
  - Preview: 150px
  - Botón: 50px
  - Resultado: 300px+

TOTAL ALTO: ~700px

Ancho necesario:
  - Input debe ser legible: 600px mínimo
  - Preview legible: 600px mínimo
  - Resultado legible: 700px mínimo

SIDEBAR ACTUAL: Muestra
  - PWR (logo)
  - Home/Radar buttons
  - Proyecto activo (si existe)
  - Tarea actual (si existe)

¿CUÁNTO APORTA SIDEBAR AQUÍ?
  ❌ PWR: Redundante (ya está implícito en el contexto)
  ❌ Home/Radar: Usuario está EN onboarding, no quiere volver (aún)
  ❌ Proyecto: No relevante (usuario nuevo, sin proyecto)
  ❌ Tarea: No relevante (estamos creando tarea AHORA)

CONCLUSIÓN: Sidebar aporta ~0% en onboarding, ocupa ~25% de espacio
```

#### ESTADO B: Nueva tarea
```
Contenido principal necesario:
  - Título: "¿Qué necesitas hacer ahora?" (50px)
  - Input: 120px
  - Ejemplos: 40px
  - Preview: 150px
  - Botón: 50px
  - Resultado: 300px+

ANCHO NECESARIO: 600px+ (input legible)

SIDEBAR ACTUAL: Muestra
  - PWR (logo)
  - Home/Radar buttons ← User PODRÍA querer volver
  - Proyecto activo ← SÍ relevante (contexto)
  - Tarea actual ← NO relevante (creando tarea nueva)

¿CUÁNTO APORTA SIDEBAR AQUÍ?
  ✅ Home button: +20% valor (user podría querer volver)
  ✅ Proyecto activo: +15% valor (contexto)
  ❌ Radar: 0% (no relevante)
  ❌ Tarea actual: 0% (contradictorio)

CONCLUSIÓN: Sidebar aporta ~35% de valor, ocupa ~25% de espacio
BALANCE: Negativo (-) en espacio
```

#### ESTADO C: Home (navegación)
```
Contenido principal necesario:
  - Grid de tareas (3 cols)
  - Grid de proyectos (2 cols)
  - Botones de acción

ANCHO NECESARIO: 1200px+ (grids bien distribuidos)

SIDEBAR ACTUAL: Muestra
  - PWR (logo)
  - Home/Radar buttons ← Estamos EN home
  - Proyecto activo (si existe) ← Navegación a proyecto
  - Tarea actual (si existe) ← Navegación a tarea

¿CUÁNTO APORTA SIDEBAR AQUÍ?
  ✅ Home button: -% (ya estamos)
  ✅ Radar: +30% valor (navegación paralela)
  ✅ Proyecto/Tarea: +40% valor (contexto rápido)

CONCLUSIÓN: Sidebar aporta ~70% de valor, ocupa ~25% de espacio
BALANCE: Positivo (+) en espacio
```

#### ESTADO D: Radar (exploración)
```
Similar a Home: Sidebar es contexto útil.
BALANCE: Positivo (+)
```

---

## 2. QUÉ GANAMOS SI ONBOARDING/NEW_TASK PIERDEN SIDEBAR

### Ganancia de espacio útil

#### Opción A: Sin sidebar completamente
```
ANTES:
[Sidebar 25%] | [Main 75%]

DESPUÉS:
[Main 100% con padding]

Ganancia: +25% de espacio horizontal
Ancho disponible: 1440px → 1400px (máximo)

Impacto en flujo:
✅ Input puede ser más ancho (mejor para lectura)
✅ Preview más legible (más columnas de datos si aplica)
✅ Flujo menos "apretado"
✅ Menos necesidad de scroll horizontal
```

#### Opción B: Sidebar colapsada
```
ANTES:
[Sidebar 25%] | [Main 75%]

DESPUÉS:
[Sidebar icon] | [Main ~95%]

Ganancia: +15-20% de espacio
Ancho disponible: 1440px → 1300px

Impacto:
✅ Espacio significativo pero no completo
✅ Navegación "dormida" pero disponible
✅ Menos impacto visual que sin sidebar
```

#### Opción C: Header mínimo arriba
```
ANTES:
[Sidebar 25%] | [Main 75%]

DESPUÉS:
[Header compacto arriba con 3 botones]
[Main 100%]

Ganancia: +25% de espacio (sin sidebar)
Plus: Navegación en header (móvil-friendly)

Impacto:
✅ Espacio máximo
✅ Navegación visible pero no invasiva
✅ Móvil-friendly bonus
```

---

## 3. CÓMO RESOLVER NAVEGACIÓN MÍNIMA SIN PERDER ORIENTACIÓN

### Opción A: Sin sidebar, header top mínimo en flujos

```
┌─────────────────────────────────────────────┐
│ 🏠 Home   │ 📡 Radar  │ PWR                 │
├─────────────────────────────────────────────┤
│                                             │
│  ¿Cuál es tu tarea?                        │
│  [Input 100%]                              │
│  [Preview 100%]                            │
│  [Botón]                                    │
│                                             │
└─────────────────────────────────────────────┘
```

**Ventajas:**
- ✅ Navegación siempre accesible (top)
- ✅ Máximo espacio para flujo
- ✅ Móvil-friendly (header colapsable)
- ✅ PWR logo visible (contexto)

**Desventajas:**
- ❌ Header compite visualmente con contenido
- ❌ Usuarios pierden contexto de proyecto (si existe)

---

### Opción B: Sidebar colapsada en flujos

```
┌──┬─────────────────────────────────────────┐
│≡ │  ¿Cuál es tu tarea?                    │
├──┤  [Input ~93%]                          │
│  │  [Preview ~93%]                        │
│  │  [Botón]                                │
│  │                                         │
│  │  [Proyecto contexto si es relevante]   │
│  │                                         │
└──┴─────────────────────────────────────────┘
```

**Ventajas:**
- ✅ Espacio recuperado (+15-20%)
- ✅ Navegación "dormida" pero accesible
- ✅ Contexto parcial visible si expandes
- ✅ Transición suave (user puede colapsar/expandir)

**Desventajas:**
- ❌ Todavía ocupa espacio (ícono ~40px)
- ❌ Requiere clic para ver contexto

---

### Opción C: Sin sidebar + contexto mínimo en content

```
┌─────────────────────────────────────────┐
│ 🏠 Home  📡 Radar                      │
├─────────────────────────────────────────┤
│                                        │
│  ¿Cuál es tu tarea?                   │
│  [Input 100%]                         │
│                                        │
│  [Preview 100%]                       │
│                                        │
│  [Botón]                              │
│                                        │
│ Proyecto: Mi primer proyecto (caption) │ ← Si relevante
│ Tarea: ... (caption)                   │ ← Si relevante
│                                        │
└─────────────────────────────────────────┘
```

**Ventajas:**
- ✅ Espacio máximo para flujo (+25%)
- ✅ Contexto visible si relevante (bottom captions)
- ✅ Navegación top (simple, clean)
- ✅ Más móvil-friendly que sidebar

**Desventajas:**
- ❌ Contexto "abajo" (no es natural)
- ❌ Requiere scroll para ver contexto

---

## 4. COMPARATIVA DE 3 OPCIONES

| Aspecto | Sin sidebar | Sidebar colapsada | Header + content |
|---------|------------|------------------|-----------------|
| **Espacio ganado** | +25% | +15-20% | +25% |
| **Navegación accesible** | Sí (top) | Sí (icon) | Sí (top) |
| **Contexto visible** | No | Sí (collapsed) | Sí (caption) |
| **Apariencia limpia** | ✅ Muy | ✅ Media | ✅ Muy |
| **Móvil-friendly** | ✅ Sí | ⚠️ Medio | ✅ Sí |
| **Transición user** | ⚠️ Brusca | ✅ Suave | ✅ Natural |
| **Esfuerzo implementación** | 🔴 Alto | 🟡 Medio | ✅ Bajo |

---

## 5. ANÁLISIS POR ESTADO

### ONBOARDING (nuevo usuario sin proyecto)
```
Necesita:
  - Escribir tarea (espacio máximo)
  - Ver propuesta (legible)
  - Clicando botón (claro)

NO necesita:
  - Contexto de proyecto (no existe)
  - Volver a home (está empezando)
  - Radar (irrelevante)

SIDEBAR: aporta 0%, ocupa 25%
RECOMENDACIÓN: ❌ Remover completamente en onboarding
```

### NUEVA TAREA (con proyecto)
```
Necesita:
  - Escribir tarea (espacio máximo)
  - Ver propuesta (legible)
  - Recordar proyecto (contexto)
  - Poder volver a home (si se arrepiente)

SIDEBAR: aporta 35%, ocupa 25%
RECOMENDACIÓN: 🤔 Colapsada es buen balance
```

### HOME (navegación)
```
Necesita:
  - Grids amplios (3 cols tareas, 2 cols proyectos)
  - Acceso rápido a Radar
  - Contexto de proyecto actual (si existe)

SIDEBAR: aporta 70%, ocupa 25%
RECOMENDACIÓN: ✅ Mantener completamente
```

### RADAR (exploración)
```
Similar a HOME.
RECOMENDACIÓN: ✅ Mantener completamente
```

---

## 6. RECOMENDACIÓN CLARA

### DECISIÓN DE DISEÑO RECOMENDADA:

```
FLUJOS (onboarding, nueva_tarea, primer_resultado):
  ❌ QUITAR SIDEBAR COMPLETAMENTE

  Por qué:
    - Sidebar no aporta contexto útil (usuario nuevo o creando tarea)
    - Ocupa 25% de espacio crítico
    - Navegación puede ir en header top (simple)
    - Ganancia: +25% espacio horizontal
    - Usuario enfocado en ESCRIBIR, no navegar

  Implementación:
    - Header mínimo: 🏠 Home | 📡 Radar | PWR
    - Sin st.sidebar en onboarding_view() y new_task_view()
    - Input aprovecha espacio máximo
    - Flujo es 100% horizontal


NAVEGACIÓN (home, radar, proyecto):
  ✅ MANTENER SIDEBAR COMPLETAMENTE

  Por qué:
    - Sidebar aporta 70% de valor (contexto + navegación)
    - Espacio no es crítico (grids son responsivos)
    - User está navegando, no escribiendo
    - Contexto rápido de proyecto/tarea es útil
    - Usuario espera sidebar en navegación


TRANSICIÓN FLUIDA:
  - User ve header mínimo en onboarding
  - Al terminar → Home aparece con sidebar
  - Al clicar "Nueva tarea" → Sidebar desaparece, header aparece
  - Al volver a Home → Sidebar reaparece
  - Sensación: Sidebar se "duerme" en flujos
```

---

## 7. IMPACTO VISUAL ESPERADO

### ANTES (G4):
```
[Sidebar] [Input 90% → 700px]
         [Preview legible pero apretado]
         [Resultado comprimido]
```

### DESPUÉS (Sidebar hide en flujos):
```
[Header mínimo]
[Input 100% → 1300px]
[Preview muy legible, espacio respira]
[Resultado con respacio óptimo]
```

**Ganancia perceptual:**
- ✅ Input parece MÁS protagonista (no compite con sidebar)
- ✅ Preview más legible (menos "apretujo")
- ✅ Flujo respira (menos densidad visual)
- ✅ Enfoque en tarea, no en navegación

---

## 8. IMPLEMENTACIÓN TÉCNICA (NO HACER TODAVÍA)

### Opción A: Sidebar condicional en main()

```python
def main():
    # Mostrar sidebar solo en navegación
    current_view = st.session_state.get("view", "home")
    show_sidebar = current_view not in ["onboarding", "new_task"]

    if show_sidebar:
        with st.sidebar:
            # Sidebar content

    # Header mínimo en flujos
    if not show_sidebar:
        col1, col2, col3 = st.columns([0.3, 0.3, 0.4])
        with col1:
            if st.button("🏠 Home"):...
        with col2:
            if st.button("📡 Radar"):...
        with col3:
            st.markdown("**PWR**")
        st.divider()

    # Routing como ahora
```

**Complejidad:** 🔴 Alta (toca routing)
**Riesgo:** 🟡 Medio (cambios en main())

---

## CONCLUSIÓN

**YO HARÍA:**

✅ **QUITAR SIDEBAR en flujos (onboarding, nueva tarea)**
  - Header mínimo arriba (3 botones)
  - Input protagonista al 100%
  - Ganancia: +25% espacio horizontal
  - User enfocado: escribir, no navegar

✅ **MANTENER SIDEBAR en navegación (home, radar, proyecto)**
  - Contexto rápido útil
  - Grids responsivos (espacio no crítico)
  - User necesita navegación

**RESULTADO FINAL:**
- Flujos respiran y enfocados
- Navegación mantiene contexto
- Transición natural: sidebar "duerme" en flujos
- UX mucho más clara: "aquí escribo" vs "aquí navego"

---

**Próximo paso:** Aprobación para implementar esta decisión de layout
