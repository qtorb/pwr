# G3: FIRST-TASK FLOW EXPLÍCITO — DIAGNÓSTICO

## PROBLEMA IDENTIFICADO

Después de G2, los **estados están separados** (A/B/C) pero el **flujo principal sigue confuso**.

Usuario no sabe:
- ¿Cuál es mi primer paso? (describir tarea? entrar a proyecto? ver historial?)
- ¿Cuál es el siguiente? (después de describir, ¿ahora qué?)
- ¿Qué hace cada acción? (¿clickeo "Generar" o "Empezar"? ¿son iguales?)
- ¿Estoy creando algo nuevo o retomando? (¿dónde está mi trabajo anterior?)

**Root cause:** Hay demasiadas **acciones principales compitiendo** al mismo nivel.

---

## 1. DIAGNÓSTICO: ACCIONES COMPITIENDO HOY

### En ESTADO A (Onboarding):

```
Pantalla ve simultáneamente:
- [Resume] [Escribe] [Analiza]     ← Quick starts (opcionales)
- [Input]                           ← O entra tu propia
- [Decision preview]                ← O ve propuesta (si tiene input)
- [✨ Empezar]                     ← CTA primario
- [Resultado + 3 CTAs]              ← Si ejecutó

CONFUSIÓN: ¿Debo clickear un ejemplo O escribir mi propia? ¿Empezar es ejecutar?
```

### En ESTADO B (Nueva tarea):

```
Pantalla ve:
- [← Volver]                        ← Salida (pero está perdida arriba)
- [Input 90px]                      ← Describir
- [Decision preview]                ← Si escribo
- [Contexto opcional]               ← Expandible
- [✨ Generar propuesta]            ← CTA primario (¿igual que "Empezar"?)

CONFUSIÓN: ¿"Generar" vs "Empezar"? ¿Ejecuta automáticamente o solo propone?
```

### En ESTADO C (Home):

```
Pantalla ve:
- Sidebar izquierdo                 ← Proyectos + navegación
- "Trabajo en progreso" (grid)      ← Retoma trabajo pasado
- "Mis proyectos" (grid)            ← Navega proyectos
- [➕ Nueva tarea]                  ← Crear nuevo
- [➕ Crear proyecto]               ← Crear proyecto

CONFUSIÓN: ¿Debo retomar una tarea O clickear "Nueva tarea"? ¿Qué es lo normal?
```

### Sidebar izquierdo:

```
- 🏠 Home
- 📡 Radar
- [Divider]
- 📁 Proyecto activo (si existe)
- [Proyectos: lista]

RUIDO: ¿Es navegación? ¿Es contexto? ¿Es necesario? ¿Duplica lo de Home?
```

---

## 2. QUÉ ACCIONES PRINCIPALES ESTÁN COMPITIENDO

### Nivel de confusión actual:

| Acción | Dónde está | Propósito | Claridad |
|--------|-----------|----------|----------|
| **Describir tarea** | Input (A/B) | Crear algo nuevo | 🟡 Menos clara que debería |
| **Click ejemplo** | Botones (A) | Quick start tarea | 🔴 ¿Por qué esto en lugar de input? |
| **Ver propuesta** | Decision preview (A/B) | Verificar decisión router | 🟡 Parece auto (no pide acción) |
| **Empezar** | Botón (A) | Ejecutar tarea | 🟡 ¿Diferencia con "Generar"? |
| **Generar propuesta** | Botón (B) | Ejecutar tarea | 🔴 ¿Mismo que "Empezar"? Nombre confuso |
| **Continuar tarea** | Card (C) | Retomar trabajo | 🟡 ¿Vs "Nueva tarea"? |
| **Nueva tarea** | Botón (C) | Crear tarea nueva | 🟡 ¿Diferencia con "Describir"? |
| **Crear proyecto** | Botón/Modal (C) | Crear proyecto | ✅ Claro |
| **Radar** | Tab/Sidebar | Explorar modelos | 🟡 ¿Es necesario en flujo principal? |
| **Home/Proyectos** | Sidebar | Navegar | 🟡 ¿Por qué está aquí si Home ya es visible? |

**Síntesis:** 7-8 acciones compitiendo, 3-4 haciendo casi lo mismo, nombres inconsistentes.

---

## 3. CUÁL DEBERÍA SER LA ÚNICA ACCIÓN PRINCIPAL EN CADA ESTADO

### Propuesta: **Un CTA primario por estado**

#### **ESTADO A (Onboarding):**

**Única acción principal:** Describir tarea → Ejecutar

```
Flujo lineal:
  1. "¿Cuál es tu tarea?" [Input]
  2. [Ve propuesta automáticamente]
  3. [✨ Ejecutar]  ← ÚNICO CTA primario

Secundarias (muy discretas):
  - [Resume] [Escribe] [Analiza] (ejemplos, no botones prominentes)
  - [Otra tarea] (después de resultado, para iterar)

Desaparece:
  - Radar en tab principal (link discreta abajo)
  - Múltiples CTAs compitiendo
```

#### **ESTADO B (Nueva tarea):**

**Única acción principal:** Describir → Propuesta → Generar

```
Flujo lineal:
  1. "¿Qué necesitas?" [Input]
  2. [Ve propuesta automáticamente]
  3. [Contexto opcional] (expander, no obliga)
  4. [✨ Generar] ← ÚNICO CTA primario

Secundarias (discretas):
  - [← Volver] (pequeño botón, esquina)
  - [Copiar resultado] (solo si hay resultado)

Desaparece:
  - Nada. B es ya limpio.
```

#### **ESTADO C (Home):**

**Única acción principal:** ¿Retomar O crear?

```
Opción 1 (Propuesta):
  - Pregunta visual clara: "¿Qué quieres hacer?"
  - Dos caminos obvios:
    * [Retomar trabajo] (grid tareas recientes)
    * [➕ Crear nueva tarea] (CTA primario)
  - Secundario: [Crear proyecto] (para power users)

Desaparece:
  - Sidebar izquierdo (o drásticamente simplificado)
  - Radar
  - Proyectos en grid (tabindex menor)
```

---

## 4. CONVERTIR PANTALLA EN FLUJO LINEAL (NO MODULAR)

### Problema actual: Modular

```
Pantalla A (Onboarding):
  [Título]
  [Explicación]
  [Tabs]
  [Ejemplos] [Input] [Preview] [Button]
  [Resultado] [3 CTAs]

Usuario: "Hay demasiados elementos, ¿cuál es lo primero?"
```

### Propuesta: Lineal (secuencial)

```
Pantalla A (Onboarding):

[1] DESCRIBE TU TAREA
    [Input 90px: "Resume este documento..."]

[2] CÓMO LO VAMOS A RESOLVER
    [Decision preview: "Tarea clara → Modo rápido"]

[3] EJECUTA
    [✨ Empezar]

[4] RESULTADO
    [Output completo]
    [✓ Guardado]
    [3 CTAs]

[Opcional]
    [Radar link discreta]
```

**Patrón:** Cada sección aparece secuencialmente. El siguiente paso es **siempre visible**.

```
Pantalla B (Nueva tarea):

[← Volver]

[1] ¿QUÉ NECESITAS?
    [Input 90px]

[2] CÓMO LO VAMOS A RESOLVER
    [Decision preview]

[3] DETALLES (opcional)
    [Contexto expandible]

[4] EJECUTA
    [✨ Generar]
```

```
Pantalla C (Home):

¿QUÉ QUIERES HACER?

[Retomar trabajo]
  [Grid: tareas recientes]

[O crear algo nuevo]
  [➕ Nueva tarea]

[Avanzado]
  [➕ Crear proyecto] (discreto)
```

**Principio:** Cada sección responde una pregunta. Flujo descendente. Sin sidebar compitiendo.

---

## 5. PAPEL DEL MENÚ LATERAL (SIDEBAR)

### Análisis actual:

```
Sidebar ve:
├─ 🏠 Home
├─ 📡 Radar
├─ [Divider]
├─ 📁 Proyecto activo (si existe)
└─ [Lista proyectos]

Problemas:
1. Duplica lo que ves en Home (proyectos)
2. Radar es accesible pero no necesario en flujo principal
3. Ocupa 20% del ancho
4. Añade "profundidad" (proyecto activo) que confunde
5. User tiene que pensar: ¿Sidebar O Home?
```

### 3 Opciones:

#### **Opción 1: Eliminar (Radical)**
```
Sidebar vacío O solo logo
Home es la única navegación
Pro: Máxima claridad
Con: Perder contexto de "proyecto activo"
Riesgo: User pierde trace de dónde está
```

#### **Opción 2: Simplificar radicalmente**
```
Sidebar:
├─ 🏠 Home
├─ 📡 Radar
└─ [Nada más]

Pro: Navegación principal clara
Con: Nada de contexto de proyecto
Beneficio: User decide en Home qué hacer
```

#### **Opción 3: Contexto-only (Recomendado)**
```
Sidebar:
├─ 🏠 Home (siempre)
├─ 📡 Radar (siempre)
├─ [Si proyecto abierto:]
│  └─ 📁 Proyecto activo (link a project_view)
└─ [Si tarea seleccionada:]
   └─ 📌 Tarea actual (nombre corto)

Pro: Contexto cuando es útil, sin ruido cuando no
Con: Más lógica condicional
Beneficio: Sidebar es "espejo del estado"
```

**Recomendación:** **Opción 3** (contexto-only)

Rationale:
- Si user está en Home, sidebar es simple (Home + Radar)
- Si user abre un proyecto, sidebar muestra "📁 Proyecto X" (visual anchor)
- Si user tiene tarea seleccionada, sidebar muestra "📌 Tarea X"
- Sidebar nunca compite con el contenido, solo refleja contexto

---

## 6. QUÉ DESAPARECE O QUEDA SECUNDARIO

### En ESTADO A (Onboarding):

| Elemento | Acción | Por qué |
|----------|--------|--------|
| Ejemplos [Resume/Escribe/Analiza] | ⬇️ Secundario | Quick start, no acción principal |
| Tabs Home/Radar | Radar → link discreta | Input es acción 1 |
| Decision preview | ✅ Automático | Se muestra, no pide acción |
| Resultado + 3 CTAs | ✅ Visible | Es paso 4 del flujo |
| Micro-guía | Desaparece | Texto explicativo innecesario |

### En ESTADO B (Nueva tarea):

| Elemento | Acción | Por qué |
|----------|--------|--------|
| Botón "← Volver" | Discreto (pequeño) | Salida, no acción principal |
| Contexto expandible | ✅ Mantener | Paso 3 (opcional pero visible) |
| Radar link | Desaparece | No entra en flujo principal |

### En ESTADO C (Home):

| Elemento | Acción | Por qué |
|----------|--------|--------|
| Sidebar con proyectos | ⬇️ Desaparece (o contexto-only) | Duplica Home |
| "Trabajo en progreso" | ✅ Visible (primera opción) | Acción 1: ¿Retomar? |
| "Nueva tarea" | ✅ CTA primario (segunda opción) | Acción 2: ¿Crear? |
| "Crear proyecto" | ⬇️ Muy discreto | Power-user feature |
| Radar tab | Desaparece (o link abajo) | No es navegación principal |

---

## 7. VALIDACIÓN: ¿PRÓXIMO PASO INTUITIVO?

### Test: "Sin instrucciones, ¿qué haces?"

#### **ESTADO A (Onboarding):**

```
Observar sin hablar:
- ¿Mira el input primero?
- ¿Clickea un ejemplo O escribe?
- ¿Entiende que "Empezar" ejecuta?
- ¿Sabe qué hacer después de resultado?

ÉXITO si: "Ah, escribo... veo la propuesta... clico Empezar"
FALLO si: "¿Qué es esto? ¿Los botones de arriba?"
```

#### **ESTADO B (Nueva tarea):**

```
Observar sin hablar:
- ¿Ve input como acción 1?
- ¿Entiende que decision preview es auto?
- ¿Sabe si contexto es obligatorio?
- ¿Entiende diferencia entre "Generar" y "Empezar"?

ÉXITO si: "Escribo, veo qué mode elige, genero"
FALLO si: "¿Qué es esto vs la otra pantalla?"
```

#### **ESTADO C (Home):**

```
Observar sin hablar:
- ¿Ve claramente "Retomar" vs "Crear"?
- ¿Sabe que está en Home (no en proyecto)?
- ¿Ignora sidebar naturalmente?
- ¿Siguiente acción es obvia?

ÉXITO si: "Veo mis tareas, puedo retomar o crear"
FALLO si: "¿Dónde estoy? ¿Qué es el sidebar?"
```

### Métrica principal:

**"Sin leer texto, ¿el siguiente paso es obvio?"**

Si la respuesta es SÍ → G3 ganó.

---

## 8. PATRÓN STREAMLIT RECOMENDADO

### Opciones evaluadas:

#### **Opción A: Una sola columna principal**

```python
st.title("¿Cuál es tu tarea?")
st.write("[Paso 1]")

input = st.text_area("...", height=90)

if input:
    st.write("[Paso 2]")
    decision = show_preview(input)

    st.write("[Paso 3]")
    if st.button("Ejecutar"):
        result = execute(input)
        st.write("[Paso 4]")
        show_result(result)
```

**Pro:** Muy lineal, flujo vertical claro
**Con:** Responsive trickier en mobile
**Mejor para:** Flujos de 3-5 pasos

#### **Opción B: Pasos secuenciales (con contadores)**

```python
st.header("1. Describe tu tarea")
input = st.text_area("...")

if input:
    st.header("2. Cómo lo resolvemos")
    decision = show_preview(input)

    st.header("3. Ejecuta")
    if st.button("Empezar"):
        st.header("4. Resultado")
        result = execute(input)
        show_result(result)
```

**Pro:** Muy claro (step 1, 2, 3...)
**Con:** Headers repetitivos
**Mejor para:** Wizards, onboarding

#### **Opción C: Contenedores condicionales**

```python
col1, col2 = st.columns([1, 0.2])

with col1:
    st.markdown("### ¿Cuál es tu tarea?")
    input = st.text_area("...")

    if input.strip():
        st.markdown("### Propuesta del Router")
        show_preview(input)

        if st.button("Ejecutar"):
            st.markdown("### Resultado")
            show_result(execute(input))
```

**Pro:** Estructura clara, responsive
**Con:** Menos lineal que A
**Mejor para:** Multi-state flows

### **RECOMENDACIÓN: Opción B + Opción C híbrido**

```python
# Sidebbar context-only (Opción 3)
with st.sidebar:
    st.markdown("### PWR")
    if st.session_state.get("active_project"):
        st.caption(f"📁 {project['name']}")

# Main: Secuencial con contenedores

st.markdown("### 1. ¿Cuál es tu tarea?")
input = st.text_area("", placeholder="...", height=90)

if input.strip():
    st.markdown("### 2. Cómo lo resolvemos")
    decision = show_preview(input)

    st.markdown("### 3. Ejecuta")
    if st.button("✨ Empezar", type="primary"):
        st.markdown("### 4. Resultado")
        result = execute(input)
        show_result(result)
```

**Resultado:** Flujo vertical lineal, sidebar minimalista, máxima claridad.

---

## STATUS TECH REAL

| Aspecto | Estado | Detalles |
|---------|--------|----------|
| **Diagnóstico** | ✅ Completo | 7-8 acciones compitiendo identificadas |
| **Flujo principal** | 🟡 Encontrado | 3-4 pasos máximo por estado |
| **Acciones claras** | 🟡 Propuesto | Un CTA primario por estado |
| **Sidebar** | 🟡 Evaluado | Opción 3 (contexto-only) recomendada |
| **Patrón Streamlit** | ✅ Definido | Híbrido B+C (secuencial + contenedores) |
| **Validación** | ✅ Método | Observación sin instrucciones ("próximo paso obvio?") |
| **Próximo paso** | ⏳ Microplan | G3 Microplan (desapariciones + cambios) |

---

## CONCLUSIÓN

**Problema:** Múltiples acciones compitiendo, flujo no lineal, sidebar duplica.

**Solución G3:**
- Un CTA primario por estado (describir → ejecutar → retomar/crear)
- Flujo vertical, pasos secuenciales
- Sidebar contexto-only (no duplica)
- Streamlit patrón híbrido B+C

**Siguiente:** Microplan G3 que detalle desapariciones + cambios específicos.

---

**FIN DE DIAGNÓSTICO G3**
