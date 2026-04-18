# G4: DIAGNÓSTICO — Jerarquía Visual del Onboarding

## PROBLEMA DETECTADO

Validación de G3 falló: **la secuencia no se entiende ni siquiera pensando**.

**Raíz:** No es lógica de pasos. Es **jerarquía visual y composición**.

---

## 1. ANÁLISIS VISUAL ACTUAL (G3 onboarding_view)

### Flujo visual que VE el usuario:

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  🚀 Portable Work Router        ← TITLE (demasiado grande) │
│  [Logo prominence innecesaria]                              │
│                                                             │
│  Describe tu tarea y PWR te ayuda a:  ← Explicación larga │
│  - Trabajar con más claridad                              │
│  - Entender por qué                                       │
│  - Guardar y reutilizar                                   │
│  [Requiere LECTURA, abstracto]                            │
│                                                             │
│  [Espaciado]                                               │
│                                                             │
│  ### 1. ¿Cuál es tu tarea?   ← Number + header (pierde se)│
│  [Input 90px]                 ← PROTAGONISTA pero 4º en  │
│  [placeholder]                   jerarquía visual        │
│                                                             │
│  💡 Ejemplos: Resume, Escribe, Analiza  ← Invisible      │
│  [Caption tiny]                                           │
│                                                             │
│  [Espaciado]                                               │
│                                                             │
│  ### 2. Cómo lo vamos a resolver    ← CONDICIONAL + header│
│  [Decision preview]            ← Requiere procesamiento │
│                                  visual cognitivo        │
│                                                             │
│  [Espaciado]                                               │
│                                                             │
│  ### 3. Ejecuta               ← CONDICIONAL + header      │
│  [✨ Empezar]                 ← Primary button, pero ¿dónde?
│                                                             │
│  [Espaciado]                                               │
│                                                             │
│  ### 4. Resultado             ← CONDICIONAL + header      │
│  [Display if ready]                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Problema visual desglosado:

| Aspecto | Hoy | Debería ser |
|---------|-----|-------------|
| **Elemento 1** | 🚀 Título PWR (grande) | INPUT DIRECTO (protagonista) |
| **Elemento 2** | Explicación 3 puntos (larga) | ELIMINADO (ruido cognitivo) |
| **Elemento 3** | Espacios múltiples | COLAPSADOS (densidad) |
| **Elemento 4** | Header "### 1. ¿Cuál..." | ELIMINADO (confunde más) |
| **Elemento 5** | Input 90px | AMPLIADO (protagonista) |
| **Elemento 6** | Caption "Ejemplos" | VISIBLE (discreta pero presente) |
| **Elemento 7** | Numbers 1,2,3,4 | ELIMINADOS (no ayudan) |
| **Elemento 8** | Headers h3 | ELIMINADOS (crean falsos pasos) |

---

## 2. QUÉ COMPITE VISUALMENTE HOY

### Competidores de atención:
1. **🚀 Portable Work Router** (Title)
   - Tamaño grande
   - Innecesario (PWR ya en sidebar)
   - **Peso visual:** ALTO
   - **Utilidad:** CERO

2. **Explicación 3 puntos**
   - "Describe tu tarea..."
   - Abstracto, requiere lectura
   - **Peso visual:** MEDIO-ALTO
   - **Utilidad:** BAJO (confunde antes de hacer)

3. **Números "1, 2, 3, 4"** (headers h3)
   - Sugieren "pasos secuenciales"
   - Pero solo el 1 es visible sin input
   - **Peso visual:** BAJO
   - **Utilidad:** NEGATIVA (rompen flujo esperado)

4. **Input 90px**
   - DEBERÍA ser protagonista
   - Pero viene después de mucho ruido
   - **Peso visual:** BAJO (debería ser ALTO)
   - **Utilidad:** CRÍTICA (pero no está clara)

5. **Caption "Ejemplos"** (💡 Resume, Escribe, Analiza)
   - Invisible por tamaño
   - **Peso visual:** CASI NADA
   - **Utilidad:** MEDIA (pero no se ve)

---

## 3. CUÁL DEBERÍA SER EL FOCO DOMINANTE

**INPUT es el único elemento que importa.**

Todo debe **apuntar hacia el INPUT** de forma inmediata:

```
VISUALIZACIÓN CORRECTA:

┌──────────────────────────────────────────┐
│                                          │
│  ¿Cuál es tu tarea?                     │ ← Copy simple, natural
│  [INPUT 120px+ - PROTAGONISTA]          │
│  [placeholder claro: "resume un..."]    │
│                                          │
│  Ejemplo rápido: Resume, Escribe        │ ← Sugestiones visibles
│                                          │
│                                          │
│  [PROPUESTA - aparece si tiene input]   │
│  [BOTÓN - aparece si input]             │
│  [RESULTADO - aparece si completado]    │
│                                          │
└──────────────────────────────────────────┘
```

**El foco está 100% en: ESCRIBIR → VER → EJECUTAR → OBTENER**

Sin intermediarios conceptuales (números, explicaciones).

---

## 4. QUÉ BLOQUES SOBRAN O TIENEN DEMASIADO PESO

### SOBRAN COMPLETAMENTE:

1. **`st.title("🚀 Portable Work Router")`**
   - PWR ya visible en sidebar
   - Es redundancia
   - **Acción:** ELIMINAR

2. **`st.write("""Describe tu tarea y PWR...""")` — Explicación 3 puntos**
   - Abstracto
   - Requiere lectura
   - Confunde PRE-USO
   - **Acción:** ELIMINAR

3. **`st.markdown("### 1. ¿Cuál es tu tarea?")` — Header numérico**
   - Los números no ayudan
   - Hacen parecer que hay más pasos de los que hay
   - **Acción:** ELIMINAR (o reemplazar por copy simple)

4. **`st.write("")` — Espacios múltiples**
   - Crean "pasos" visuales falsos
   - **Acción:** REDUCIR (máximo 1 espacio)

### PIERDEN PESO (pero siguen):

1. **Caption "Ejemplos"** (💡 Resume, Escribe, Analiza)
   - Es invisible
   - **Acción:** HACERLA VISIBLE (pero discreta)

2. **`st.markdown("### 2. Cómo lo vamos a resolver")`**
   - Aparece condicional (está bien)
   - Pero el header h3 es innecesario
   - **Acción:** ELIMINAR header, mantener display_decision_preview()

3. **`st.markdown("### 3. Ejecuta")`**
   - Innecesario
   - El botón habla por sí
   - **Acción:** ELIMINAR

4. **`st.markdown("### 4. Resultado")`**
   - Innecesario
   - El resultado habla por sí
   - **Acción:** ELIMINAR

---

## 5. CÓMO REORGANIZAR PARA QUE LA SECUENCIA SE SIENTA

### Principio: DENSIDAD + AUTOMATISMO

```
NUEVA ESTRUCTURA PROPUESTA:

┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  ¿Cuál es tu tarea?                                        │
│  [Input 120px - PROTAGONISTA]                              │
│  Ejemplo rápido: Resume, Escribe, Analiza                 │
│                                                             │
│  [SI input tiene contenido] ↓                             │
│  ─────────────────────────────────────────────────────────│
│                                                             │
│  [Decision preview - aparece automático]                   │
│                                                             │
│  [✨ Empezar] ← PRIMARY button (visible si input)          │
│                                                             │
│  ─────────────────────────────────────────────────────────│
│                                                             │
│  [SI ejecutado] ↓                                         │
│                                                             │
│  [Resultado] ← aparece automático                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Cambios clave:

1. **Input INMEDIATO** (primer elemento visible)
2. **Ejemplos legibles** (debajo, discreta pero visible)
3. **Sin números, sin explicaciones**
4. **Flujo por ESPACIAMIENTO VISUAL:**
   - Lo que aparece arriba = hoy
   - Lo que aparece abajo = después
5. **Densidad:** Máximo texto. No sobra nada.
6. **Automatismo:** Propuesta → Botón → Resultado aparecen SIN CLICAR

---

## 6. JERARQUÍA FINAL (Primario, Secundario, Terciario)

### PRIMARIO (lo que ves PRIMERO)
```
┌─────────────────────────────────────────┐
│ ¿Cuál es tu tarea?                      │
│ [Input 120px - el único protagonista]   │
│ Ejemplo: Resume, Escribe, Analiza       │
└─────────────────────────────────────────┘
```

**Mensajes visuales:**
- ✅ Hay un input enorme
- ✅ Sé qué meter
- ✅ Tengo ejemplos
- ✅ Siguiente paso: ESCRIBIR

---

### SECUNDARIO (aparece si escribes)
```
[Decision preview]
[✨ Empezar] ← CTA clara
```

**Mensajes visuales:**
- ✅ PWR vio lo que escribiste
- ✅ Esto es lo que va a pasar
- ✅ Siguiente paso: CLICAR BOTÓN

---

### TERCIARIO (aparece si ejecutas)
```
[Resultado]
[Copiar / Otra tarea / Ver proyecto]
```

**Mensajes visuales:**
- ✅ Está listo
- ✅ Esto fue lo que pasó
- ✅ Qué haces ahora

---

## 7. VALIDACIÓN: ¿SECUENCIA SE ENTIENDE DE UN VISTAZO?

### Test mental (sin leer):

**HOY (G3):**
- ¿Qué hago? → "Leo explicación 3 puntos" ❌
- ¿Dónde escribo? → "Busco entre números y espacios" ❌
- ¿Cuándo clicar? → "Espero a ver un número 3" ❌

**PROPUESTO (G4):**
- ¿Qué hago? → "Veo enorme input, escribo ahí" ✅
- ¿Qué pasa después? → "Veo automático algo abajo" ✅
- ¿Cuándo clicar? → "Veo botón cuando está listo" ✅

### Métrica: "Sin leer, ¿entiendes en 2 segundos?"

- **HOY (G3):** NO - requiere procesar título, explicación, números
- **PROPUESTO (G4):** SÍ - input grande, ejemplos, botón cuando importa

---

## 8. QUÉ DESAPARECERÁ (vs G3)

```
❌ st.title("🚀 Portable Work Router")
❌ st.write("""Describe tu tarea y PWR...""") - 3 puntos
❌ st.markdown("### 1. ¿Cuál es tu tarea?")
❌ st.write("") - espacios múltiples (collapse a 1-2)
❌ st.markdown("### 2. Cómo lo vamos a resolver")
❌ st.markdown("### 3. Ejecuta")
❌ st.markdown("### 4. Resultado")
```

Total: ~10 líneas de "ruido visual"

---

## 9. QUÉ QUEDARÁ (vs G3)

```
✅ Input 90px→120px
✅ Ejemplos visibles (caption o badge discreto)
✅ Decision preview (automático, sin header)
✅ Botón PRIMARY (automático)
✅ Resultado (automático, sin header)
✅ Lógica de ejecución (intacta)
✅ Session state (intacto)
```

Total: Menos líneas, más claridad visual.

---

## STATUS TÉCNICO ACTUAL

| Aspecto | Estado | Detalle |
|---------|--------|--------|
| **Código compilable** | ✅ | Syntax OK |
| **Lógica backend** | ✅ | ExecutionService sin cambios |
| **Session state** | ✅ | Intacto |
| **Routing** | ✅ | Sin cambios |
| **G4 Implementación** | 🔴 | Pendiente microplan + code |
| **Riego de G4** | ⚠️ | Muy bajo (UI pura, sin lógica) |

---

## SÍNTESIS: PROBLEMA vs SOLUCIÓN

| Aspecto | Problema | Solución |
|---------|----------|----------|
| **Foco visual** | Title + Explicación | INPUT directo |
| **Secuencia** | Números 1-4 (confunden) | Flujo por espaciamiento |
| **Densidad** | Espacios múltiples, ruido | Colapsada, solo necesario |
| **Automatismo** | Esperado pero no obvio | Propuesta + Botón auto visibles |
| **Copy** | Abstracta (3 puntos) | Simple (preguntas directas) |
| **Ejemplos** | Invisibles (caption) | Visibles pero discretos |

---

## CONCLUSIÓN DEL DIAGNÓSTICO

✅ **G3 falló por composición, no por lógica.**

**Raíz:** INPUT es protagonista pero visualmente está 4º en jerarquía.

**Solución G4:** Invertir jerarquía = INPUT primero, TODO DEMÁS apoya.

**Cambios esperados:**
- Menos líneas de código
- Mejor composición visual
- Secuencia se SIENTE, no se EXPLICA
- Validación: usuario entiende en 2 segundos sin leer

**Próximo paso:** Microplan G4 con especificaciones de composición.

---

**FIN DEL DIAGNÓSTICO**
