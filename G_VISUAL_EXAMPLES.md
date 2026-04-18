# BLOQUE G: Ejemplos Visuales Reales

## Escenario 1: Tarea ECO (Simple)

### Input del usuario
```
Resume este documento en 3 líneas
```

### Decision Preview (antes de "✨ Empezar")
```
💡 Cómo lo voy a resolver

Modo recomendado: ECO (rápido)
Motivo: Tarea de síntesis estructurada con requisitos claros

⏱️ Tiempo estimado: ~2–4s
💰 Coste estimado: bajo
```

### User clicks "✨ Empezar" → Progreso visual
```
⏳ Analizando tu tarea...
⏳ Seleccionando el mejor modo...
⏳ Ejecutando...
```

### Resultado mostrado (después de rerun)

```
═══════════════════════════════════════════════════════════

🎯 Por qué PWR eligió este modo
Tarea clara y directa: PWR eligió un modo rápido

📋 Resultado
---
Párrafo 1: El documento presenta tres puntos clave sobre [tema].
Párrafo 2: Estas recomendaciones implican cambios en [área].
Párrafo 3: La implementación requiere consideración de [factor].
---

✓ Tarea guardada en tu proyecto

[🚀 Otra tarea rápida] [📋 Copiar resultado] [📁 Crear nuevo proyecto]

💡 [Explorar modelos disponibles →] en tab Radar si quieres
   ver qué opciones tiene PWR

═══════════════════════════════════════════════════════════
```

---

## Escenario 2: Tarea RACING (Compleja)

### Input del usuario
```
Analiza este dataset de ventas y propón una estrategia de precio dinámico
```

### Decision Preview (antes de "✨ Empezar")
```
💡 Cómo lo voy a resolver

Modo recomendado: RACING (análisis profundo)
Motivo: Análisis multidimensional que requiere modelado estratégico

⏱️ Tiempo estimado: ~10–30s
💰 Coste estimado: medio-alto
```

### User clicks "✨ Empezar" → Progreso visual
```
⏳ Analizando tu tarea...
⏳ Seleccionando el mejor modo...
⏳ Ejecutando...
```

### Resultado mostrado (después de rerun)

```
═══════════════════════════════════════════════════════════

🎯 Por qué PWR eligió este modo
Tarea que necesita análisis profundo: PWR eligió un modo potente

📋 Resultado
---
## Análisis de datos de ventas

### Segmentación de clientes
- Tier 1 (Premium): 20% de volume, 60% de revenue
- Tier 2 (Estándar): 50% de volume, 35% de revenue
- Tier 3 (Precio-sensible): 30% de volume, 5% de revenue

### Estrategia de precio dinámico recomendada

#### Para Tier 1
Aumentar margen 15-20% respecto a price-point actual, mantener
disponibilidad premium.

#### Para Tier 2
Optimizar elasticidad: pequeños cambios de precio pueden mover
volume significativamente.

#### Para Tier 3
Mantener competitivo pero no subsidiar. Considerar bundle strategies.

### Métricas de éxito
- Proyectado ROI: +12-18% en 6 meses
- Riesgo de churn: bajo (segmentación mantiene valor perceived)

---

✓ Tarea guardada en tu proyecto

[🚀 Otra tarea rápida] [📋 Copiar resultado] [📁 Crear nuevo proyecto]

💡 [Explorar modelos disponibles →] en tab Radar si quieres
   ver qué opciones tiene PWR

═══════════════════════════════════════════════════════════
```

---

## Diferencias claves entre ECO y RACING en el bloque "Por qué"

### ECO
```
🎯 Por qué PWR eligió este modo
Tarea clara y directa: PWR eligió un modo rápido
```
- Copy corta y direct
- Enfatiza velocidad sin perder calidad
- User entiende: "esto es eficiente"

### RACING
```
🎯 Por qué PWR eligió este modo
Tarea que necesita análisis profundo: PWR eligió un modo potente
```
- Copy comunica complejidad
- Justifica el tiempo y recursos
- User entiende: "esto lo merece"

---

## Comportamiento de CTAs

### Escenario: Usuario clickea "🚀 Otra tarea rápida"

1. Limpia `onboard_capture_input = ""`
2. Limpia `onboard_result_ready = False`
3. `st.rerun()`
4. Interfaz vuelve al estado pre-resultado:

```
═══════════════════════════════════════════════════════════

🏠 Home | 📡 Radar

¿Cuál es tu tarea?

[Resume] [Escribe] [Analiza]

[Input vacío]

PWR analizará tu tarea y elegirá el modelo más adecuado

[✨ Empezar (disabled)]

═══════════════════════════════════════════════════════════
```

5. User puede entrar otra tarea o clickear ejemplo distinto

---

### Escenario: Usuario clickea "📋 Copiar resultado"

```
Success message (green box):
✓ Resultado copiado al portapapeles (simulado)
```

- Simula copia (en v2 será real con clipboard API)
- Desaparece después de algunos segundos
- User puede seguir con otras acciones

---

### Escenario: Usuario clickea "📁 Crear nuevo proyecto"

```
❌ Onboarding result desaparece
✅ Modal de crear proyecto aparece:

─────────────────────────────────
Crear proyecto

Nombre         [Mi nuevo proyecto]
Descripción    [            ]
Objetivo       [            ]
...
[Crear]
─────────────────────────────────
```

- Abre form modal inline
- User puede crear proyecto con más contexto
- Luego vuelve a home con nuevo proyecto

---

## Copy exacto de cada elemento

### Explanation (línea que precede el input)

```
Describe tu tarea y PWR te ayuda a:
- Trabajar con más claridad — eligiendo el enfoque adecuado
- Entender por qué — viendo cómo PWR decide
- Guardar y reutilizar — continuidad de tu trabajo
```

### Caption bajo input

```
PWR analizará tu tarea y elegirá el modelo más adecuado
```

### Button primario

```
✨ Empezar
```

### Bloque 1 titulo

```
### 🎯 Por qué PWR eligió este modo
```

### Bloque 1 copy (eco)

```
Tarea clara y directa: PWR eligió un modo rápido
```

### Bloque 1 copy (racing)

```
Tarea que necesita análisis profundo: PWR eligió un modo potente
```

### Bloque 2 titulo

```
### 📋 Resultado
```

### Bloque 2 contenido

```
[Output completo del LLM, sin edición]
```

### Bloque 3 confirmación

```
✓ Tarea guardada en tu proyecto
```

### Bloque 4 CTAs

```
Columna 1: 🚀 Otra tarea rápida
Columna 2: 📋 Copiar resultado
Columna 3: 📁 Crear nuevo proyecto
```

### Bloque 5 Radar reference

```
💡 [Explorar modelos disponibles →] en tab Radar si quieres ver qué opciones tiene PWR
```

---

## Estados de la UI a lo largo del onboarding

### Estado 1: Vacío (inicial)
- Input es null/empty
- "✨ Empezar" está disabled (grey)
- Ejemplos son clickeables
- No hay decision preview

### Estado 2: Input con contenido (sin click ejemplo)
- User escribe "Resume esto..."
- Decision preview aparece (💡 Cómo lo voy a resolver)
- "✨ Empezar" está enabled (blue)

### Estado 3: Click en ejemplo
- Input se pre-llena con ejemplo
- Decision preview aparece (calculada en la vuelta)
- "✨ Empezar" está enabled

### Estado 4: Click "✨ Empezar"
- Progress visual (⏳ 3 mensajes)
- Se bloquea input y botones
- Backend ejecuta tarea

### Estado 5: Resultado mostrado
- 3 bloques aparecen (Por qué, Resultado, Guardado)
- CTAs aparecen
- Radar reference aparece
- User puede hacer siguiente acción

---

## Responsive behavior (F3 mobile-first)

### Mobile (viewport < 600px)

- Input: 90px altura (compact)
- Ejemplos: Stack en 1 columna (o 2 en landscape)
- Resultado: Full width
- CTAs: Stack en 1 columna
- Radar link: Visible en mobile

### Tablet (viewport 600-900px)

- Input: 90px
- Ejemplos: 2 columnas
- Resultado: Full width
- CTAs: 3 columnas compactas
- Radar link: Visible

### Desktop (viewport > 900px)

- Input: 90px
- Ejemplos: 3 columnas
- Resultado: Full width
- CTAs: 3 columnas espaciosas
- Radar link: Visible

---

## Error scenarios

### Escenario: Ejecución falla

```
⏳ Analizando tu tarea...
⏳ Seleccionando el mejor modo...
⏳ Ejecutando...

[Progress placeholder limpio]

Error en ejecución: [error message]
```

- User ve error claramente
- Puede volver a intentar (editar input y click "✨ Empezar" otra vez)
- No se bloquea ni crashea

### Escenario: Proveedor no disponible

```
⚠️ No se pudo completar la ejecución

Tipo de error: provider_not_available
Detalles: Claude API not configured

→ Revisa la configuración del proveedor o conecta un motor diferente.
```

- (Esta lógica existe en project_view, puede agregarse a onboarding en v2)

---

## Transiciones (flow)

### De "¿Cuál es tu tarea?" a "Resultado"

```
User entrada         → Ejemplos disponibles
User escribe         → Decision preview (ECO/RACING)
User click "Empezar" → Progress (3 pasos)
                     → Rerun con resultado
                     → Resultado visible (3 bloques)
```

### De Resultado a "Otra tarea rápida"

```
Resultado visible    → User click "🚀 Otra tarea rápida"
                     → Input limpio
                     → Result blocks desaparecen
                     → De vuelta a "¿Cuál es tu tarea?"
```

### De Resultado a "Crear nuevo proyecto"

```
Resultado visible    → User click "📁 Crear nuevo proyecto"
                     → Modal abierto (create project form)
                     → Resultado aún visible detrás
                     → User completa form
                     → Nuevo proyecto creado
                     → Modal cierra
```

---

## Notas finales

- Todos los ejemplos usan copy REAL de la implementación
- La longitud del resultado puede variar (LLM-dependent)
- Los emojis y separadores son exactos (🎯, 📋, ✓, 💡, etc.)
- El spacing (st.write("")) mantiene densidad visual
- Responsive design ajusta automáticamente sin breakpoints CSS

---

**Ejemplos visuales precisos del BLOQUE G implementado**
