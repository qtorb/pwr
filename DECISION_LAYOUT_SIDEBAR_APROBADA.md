# DECISIÓN DE DISEÑO: Sidebar Dinámico (Dormido/Despierto)

**Estado:** ✅ APROBADA
**Fecha:** 2026-04-18
**Aplicación:** Próxima iteración (G5 o posterior)

---

## REGLA DE DISEÑO APROBADA

**"Sidebar dormida en flujos, despierta en navegación"**

### Vistas donde SIDEBAR DESAPARECE (Modo Flujo)

```
❌ onboarding_view()      (usuario nuevo, input protagonista)
❌ new_task_view()         (creando tarea, máximo enfoque)
❌ primer_resultado_view() (viendo resultado, lectura completa)
```

**Razón:** 0-35% aporte, 25% espacio crítico que el flujo necesita.

### Vistas donde SIDEBAR PERMANECE (Modo Navegación)

```
✅ home_view()            (exploración, contexto útil)
✅ radar_view()           (snapshot global, navegación)
✅ project_view()         (gestión tareas, contexto relevante)
```

**Razón:** 70%+ aporte, espacio no crítico (grids responsivos).

---

## MATIZ IMPORTANTE: Header Mínimo Muy Sobrio

En vistas de flujo, **NO** header ruidoso. Solo lo esencial:

### ❌ NO HACER (demasiado cargado)

```
┌─────────────────────────────────────────────────────────┐
│ 🏠 Home │ 📡 Radar │ ❌ │ PWR │ 🔔 Notifications │ ⚙️   │
├─────────────────────────────────────────────────────────┤
│ [Mini-navbar, breadcrumbs, search, tools, etc.]         │
│                                                         │
│  ¿Cuál es tu tarea?                                    │
│  [Input]                                               │
└─────────────────────────────────────────────────────────┘
```

### ✅ HACER (muy sobrio)

```
┌─────────────────────────────────────────────────────────┐
│ ← Volver  │  Mi primer proyecto (caption)  │  PWR       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ¿Cuál es tu tarea?                                    │
│  [Input 100% viewport]                                 │
│                                                         │
│  [Preview]                                             │
│  [Botón]                                               │
│  [Resultado]                                           │
└─────────────────────────────────────────────────────────┘
```

### Componentes del Header Mínimo

```
[← Volver]  [Contexto si aplica]  [PWR]
```

**Detalles:**
- **"← Volver":** Botón simple, vuelve a home
- **"Contexto si aplica":** Caption con nombre proyecto (solo si existe y es relevante)
  - En onboarding: NADA (usuario nuevo)
  - En new_task: "Mi primer proyecto" (contexto)
  - En resultado: NADA (ya está en contexto)
- **"PWR":** Logo/texto pequeño, orientación

**Características:**
- ✅ Máximo 40px de altura
- ✅ Una sola línea
- ✅ Caption size fonts (no headers)
- ✅ Sin colores ruidosos, sin iconos extras
- ✅ Propósito: orientación + escape, no navegación

---

## RAZÓN FUNDAMENTAL

Usuario en flujos necesita foco total en:

```
1. TAREA
   "¿Cuál es tu tarea?"
   [Input]

2. PROPUESTA
   "Esto es lo que pasaría..."
   [Preview]

3. EJECUTAR
   "Empezar"
   [Botón]

4. RESULTADO
   [Output]
   [CTAs]
```

**Sidebar + ruidosa navbar = distracción**
**Header mínimo + máximo espacio = foco**

---

## IMPLEMENTACIÓN: Pendiente de Microplan

Esta decisión queda como base para cuando se implemente. En ese momento necesitaremos:

### 1️⃣ Vistas que pierden sidebar

```python
# En main():
FLOW_VIEWS = ["onboarding", "new_task", "primer_resultado"]

if current_view not in FLOW_VIEWS:
    with st.sidebar:
        # Sidebar normal
```

**Afectadas:**
- `onboarding_view()` ← Ya modificada en G4
- `new_task_view()` ← Ya modificada en G4
- Nueva: `primer_resultado_view()` (si se crea)

---

### 2️⃣ Header mínimo que tendrán

Cada vista de flujo tendrá este header:

```python
# En onboarding_view():
st.markdown("---")  # Divider opcional
col1, col2, col3 = st.columns([0.1, 0.8, 0.1])
with col1:
    if st.button("←", key="back_onboarding"):
        st.session_state["view"] = "home"
        st.rerun()
with col2:
    st.markdown("")  # Centro vacío (balance)
with col3:
    st.markdown("**PWR**", help="Portable Work Router")

st.write("")  # Espaciado pequeño
```

---

### 3️⃣ Transición entre modo navegación y flujo

**Transición ENTRADA (home → new_task):**
```
User en home_view() [sidebar visible]
  ↓
Click "Nueva tarea"
  ↓
st.session_state["view"] = "new_task"
  ↓
st.rerun()
  ↓
main() detecta: current_view == "new_task" (en FLOW_VIEWS)
  ↓
No dibuja sidebar
  ↓
new_task_view() se llama
  ↓
Header mínimo aparece (← Volver, Proyecto, PWR)
  ↓
User ve: layout limpio, input protagonista
```

**Transición SALIDA (new_task → home):**
```
User en new_task_view() [sin sidebar]
  ↓
Click "← Volver"
  ↓
st.session_state["view"] = "home"
  ↓
st.rerun()
  ↓
main() detecta: current_view == "home" (NOT en FLOW_VIEWS)
  ↓
Dibuja sidebar (reaparece)
  ↓
home_view() se llama con sidebar
  ↓
User ve: navegación completa, contexto retorna
```

**Experiencia del usuario:**
- Natural: "Estoy navegando → clico Nueva tarea → desaparece ruido, me enfoco → clico Volver → reaparece sidebar"
- Sin brusquedad: transición es por cambio de view
- Esperada: User entiende que hay "modo flujo" y "modo navegación"

---

### 4️⃣ Validación que el ancho extra mejora claridad

**Métrica 1: Legibilidad de input**
```
ANTES (con sidebar):
  Input ancho: 1080px
  Placeholder se corta en mobile
  Text wrap innecesario

DESPUÉS (sin sidebar):
  Input ancho: 1300px
  Placeholder completo en una línea
  Text wrap solo si user escribe mucho
```

**Test:** Input placeholder debe ser completamente legible sin scroll/wrap

---

**Métrica 2: Visualización de preview**
```
ANTES (con sidebar):
  Decision preview: 1080px
  Si tiene tabla/datos: comprimido
  Lectura difícil

DESPUÉS (sin sidebar):
  Decision preview: 1300px
  Tabla/datos: espaciado respirable
  Lectura natural
```

**Test:** User no necesita scroll horizontal para leer preview

---

**Métrica 3: Jerarquía visual**
```
ANTES (con sidebar):
  Input compite con sidebar visualmente
  User no sabe dónde enfocarse
  Dos cosas demandan atención

DESPUÉS (sin sidebar):
  Input es único protagonista
  Flujo vertical es obvio
  User sabe: "esto es lo importante"
```

**Test:** Sin leer, ¿dónde mira primero el user? Debe ser el input.

---

**Métrica 4: Espacio respirable**
```
ANTES: Densidad visual alta (2 cosas lado a lado)
DESPUÉS: Densidad visual baja (1 cosa central)

Pregunta a user: "¿Se siente menos apretujo?"
```

**Test:** Debería responder sí.

---

**Métrica 5: Navegación sin confusión**
```
ANTES: Sidebar tiene botones (home, radar, contexto)
       User tentado a navegar
       Interfaz compite consigo misma

DESPUÉS: Header mínimo solo de escape
         User enfocado en tarea
         Si quiere salir, hay botón "Volver"
```

**Test:** User completa flujo sin distraerse en navegación

---

## CRITERIO DE ÉXITO

Implementación G5 (o cuando se haga) será exitosa si:

```
✅ Sidebar desaparece en onboarding/new_task/resultado
✅ Header mínimo aparece (← Volver, Contexto, PWR)
✅ Input/Preview/Resultado ocupan 100% viewport
✅ Input es visualmente protagonista
✅ Preview sin scroll horizontal
✅ User entiende transición (flujo vs navegación)
✅ User no se siente perdido (header de escape claro)
✅ 80%+ users dicen "menos apretujo, más claro"
```

---

## DECISIÓN FINAL DOCUMENTADA

Esta decisión de layout (sidebar dinámico) queda aprobada como:

1. ✅ Regla de diseño clara: dormida en flujos, despierta en navegación
2. ✅ Matiz: header mínimo muy sobrio (no ruidoso)
3. ✅ Razón: máximo foco en tarea, propuesta, ejecución, resultado
4. ✅ Base para microplan futuro con 4 implementables:
   - Qué vistas pierden sidebar
   - Qué header mínimo tendrán
   - Cómo transición entre modos
   - Cómo validar mejora en claridad

**Próxima acción:** Cuando toque implementar (G5 o posterior), abrir microplan concreto basado en esta especificación.

---

**Decisión aprobada por Albert**
**Fundamento:** Maximizar espacio horizontal en flujos, mantener contexto en navegación.
