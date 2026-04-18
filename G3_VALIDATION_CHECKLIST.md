# G3: VALIDACIÓN DE EXPERIENCIA — Testing Checklist

## Objetivo
Verificar que el siguiente paso es **siempre obvio** sin leer instrucciones.

---

## TEST 1: ONBOARDING (Usuario nuevo, sin actividad)

### Setup
```
1. Clear browser cache / new incognito window
2. En app: ensure no projects, no tasks
3. Session state: has_activity = False
```

### Flujo observado
```
[ ] Pantalla 1 carga
    [ ] Ve número "1" prominente
    [ ] Ve "¿Cuál es tu tarea?"
    [ ] Input visible (90px tall)
    [ ] Caption "💡 Ejemplos: Resume, Escribe, Analiza"

[ ] Llena input (ej: "resume este documento")
    [ ] Número "2" aparece automáticamente
    [ ] "Cómo lo vamos a resolver" visible
    [ ] Decision preview visible (sin clicar)
    [ ] Número "3" visible
    [ ] Botón "✨ Empezar" visible

[ ] Click "✨ Empezar"
    [ ] Progreso visible (analizando...)
    [ ] Número "4" aparece después
    [ ] "Resultado" visible
    [ ] Output del modelo visible
    [ ] No hay tabs, no hay sidebar clutter

[ ] Transición post-resultado
    [ ] CTAs: "Otra tarea" / "Copiar" / "Ver proyecto"
    [ ] Si click "Otra tarea" → vuelve a input (número 1)
    [ ] Input está limpio (no ve "Retoma tu trabajo")
```

### Métrica de éxito
- **SIN leer texto**, ¿usuario entiende "siguiente paso"?
  - ✅ SÍ si: números visibles, orden vertical, siguiente paso está abajo
  - ❌ NO si: confundido entre botones, tabs, o scroll arriba/abajo

### Validación cuantitativa (si tienes usuarios de prueba)
- Pregunta: "Sin instrucciones, ¿cuál es el siguiente paso?"
- ✅ ÉXITO: 80%+ responden correctamente (input → propuesta → botón → resultado)

---

## TEST 2: NUEVA TAREA (Usuario con actividad previa)

### Setup
```
1. Tener al menos 1 proyecto y 1 tarea completada
2. Estar en Home (ha_activity = True)
3. Clicar "➕ Nueva tarea"
```

### Flujo observado
```
[ ] Pantalla carga
    [ ] Header "¿Qué necesitas hacer ahora?"
    [ ] Botón "← Volver" en esquina (DISCRETO, no compite)
    [ ] Proyecto activo mencionado (caption)

[ ] Números visibles
    [ ] "### 1. ¿Qué necesitas?" (input 90px)
    [ ] Llena input

[ ] Automáticamente
    [ ] "### 2. Cómo lo vamos a resolver" aparece
    [ ] Decision preview visible
    [ ] "### 3. Detalles (opcional)"
    [ ] Expander contexto (CERRADO por defecto)
    [ ] "### 4. Ejecuta"
    [ ] Botón "✨ Generar propuesta"

[ ] Comparación con Onboarding
    [ ] ¿Patrón es idéntico? (1→2→3→4)
    [ ] ¿Usuario entiende que es "el mismo flujo pero nuevo"?

[ ] Botón "Volver"
    [ ] Click → vuelve a Home
    [ ] Input está limpio
    [ ] No ve "Retoma tu trabajo" en nueva_tarea_view

[ ] Click "Generar"
    [ ] Crea tarea
    [ ] Entra a project_view
    [ ] No hay confusión
```

### Métrica de éxito
- ¿Patrón es familiar (mismo que onboarding)?
  - ✅ SÍ si: números iguales, orden igual, solo contenido diferente
  - ❌ NO si: usuario espera algo diferente

- ¿Botón "Volver" es discreto (no distrae)?
  - ✅ SÍ si: no compete con CTAs principales
  - ❌ NO si: user se confunde entre "Volver" y "Generar"

---

## TEST 3: HOME — Navegación clara

### Setup
```
1. Estar en Home (has_activity = True)
2. Tener múltiples tareas recientes + proyectos
```

### Flujo observado
```
[ ] Pantalla estructura
    [ ] Encabezado "### 🏠 Mis tareas"
    [ ] NO hay input arriba (ese está en new_task_view)

[ ] Sección "#### Trabajo en progreso"
    [ ] Grid de tareas (3 cols en desktop)
    [ ] Botón "Continuar" por tarea
    [ ] Click → entra a project_view

[ ] Sección "#### Mis proyectos"
    [ ] Grid de proyectos (2 cols)
    [ ] Botón "Abrir" por proyecto
    [ ] Click → entra a project_view

[ ] CTAs inferiores
    [ ] "➕ Nueva tarea" (PRIMARY, prominente)
    [ ] "➕ Crear proyecto" (SECONDARY)
    [ ] Dos opciones claras: retomar vs crear

[ ] Distinción visual
    [ ] ¿Usuario entiende: "aquí retomo" vs "aquí creo"?
    [ ] Click "Nueva tarea" → ESTADO B (new_task_view)
    [ ] Click "Crear proyecto" → Modal expandible
```

### Métrica de éxito
- **Pregunta:** "¿Qué hago si quiero continuar una tarea que empecé?"
  - ✅ ÉXITO: "hago clic en Continuar" (en grid tareas)
  - ❌ FALLO: "escribo aquí arriba" (si hay input) o confundido

- **Pregunta:** "¿Qué hago si quiero empezar algo totalmente nuevo?"
  - ✅ ÉXITO: "clic en Nueva tarea" (CTA primaria)
  - ❌ FALLO: "clic en Crear proyecto" o confundido

---

## TEST 4: SIDEBAR — Contexto-only

### Observación
```
[ ] ESTADO A (Onboarding)
    [ ] Sidebar muestra: Logo PWR, Home, Radar
    [ ] NO hay "Proyecto activo"
    [ ] NO hay "Tarea actual"
    [ ] NO hay lista proyectos

[ ] ESTADO B (New task)
    [ ] Sidebar muestra: Logo PWR, Home, Radar
    [ ] IGUAL que ESTADO A

[ ] ESTADO C (Home)
    [ ] Sidebar muestra: Logo PWR, Home, Radar
    [ ] Si user abrió proyecto:
        [ ] + "📁 Proyecto activo"
        [ ] + nombre proyecto (25 chars)

[ ] ESTADO D (Project view)
    [ ] Sidebar muestra: Logo PWR, Home, Radar
    [ ] + "📁 Proyecto activo" {nombre}
    [ ] + "📌 Tarea actual" {nombre} (si task seleccionada)

[ ] Cleanliness
    [ ] Sidebar NUNCA duplica navegación
    [ ] Sidebar es "espejo del estado"
    [ ] Sidebar es mínimo (no compite)
```

### Métrica de éxito
- ¿Sidebar añade claridad o ruido?
  - ✅ ÉXITO si: usuario entiende "dónde estoy" rápidamente
  - ❌ FALLO si: sidebar duplica contenido o distrae

---

## TEST 5: TRANSICIONES — Flujo entre estados

### Scenario A: Onboarding → Home
```
[ ] Onboarding completa ejecución
[ ] Resultado visible
[ ] Click "Otra tarea rápida"
[ ] Input limpio (vuelve a número 1)
[ ] Has_activity ahora True
[ ] Siguiente rerun → home_view() se llama
[ ] Ve "Trabajo en progreso" (su tarea nueva)
```

### Scenario B: Home → New task → Home
```
[ ] Home visible
[ ] Click "Nueva tarea"
[ ] View = "new_task" → new_task_view() se llama
[ ] Llena input + contexto
[ ] Click "Volver"
[ ] View = "home" → home_view() se llama
[ ] Está en Home de nuevo
```

### Scenario C: Home → New task → Project
```
[ ] Home visible
[ ] Click "Nueva tarea"
[ ] new_task_view() se llama
[ ] Llena input + contexto
[ ] Click "Generar propuesta"
[ ] Tarea se crea
[ ] selected_task_id se asigna
[ ] Siguiente rerun: main() ve active_project_id → project_view()
```

### Métrica de éxito
- ¿Transiciones son suaves sin "saltos"?
  - ✅ ÉXITO si: usuario no ve loading innecesario, flujo es natural
  - ❌ FALLO si: reruns múltiples, saltos, confusión

---

## TEST 6: COMPORTAMIENTO DE DECISION PREVIEW

### Onboarding
```
[ ] Input vacío → NO ve "2. Cómo lo vamos a resolver"
[ ] Input "resume..." → VE automáticamente "2. Cómo..."
[ ] Decision preview visible sin clicar
[ ] Si borra input → decision preview desaparece
```

### Nueva tarea (identical)
```
[ ] Input vacío → NO ve "2. Cómo lo vamos a resolver"
[ ] Input "escribe..." → VE automáticamente "2. Cómo..."
[ ] Decision preview visible sin clicar
[ ] Mismo patrón que onboarding
```

### Métrica de éxito
- ¿Preview es automático (no requiere clic)?
  - ✅ ÉXITO si: aparece apenas user escribe
  - ❌ FALLO si: user tiene que clicar algo

---

## RESULTADO GENERAL

### Scoring

| Test | Critico | Observación | Status |
|------|---------|-------------|--------|
| Onboarding lineal | ✅ | 1→2→3→4 visible, números claros | [ ] |
| Nueva tarea lineal | ✅ | Patrón idéntico a onboarding | [ ] |
| Home navegación | ✅ | 2 opciones claras (retomar vs crear) | [ ] |
| Sidebar contexto-only | ✅ | Espejo del estado, no ruido | [ ] |
| Transiciones smooth | ✅ | Flujos sin saltos | [ ] |
| Decision preview auto | ✅ | Aparece sin clicar | [ ] |

### Pregunta final (sin instrucciones):
**"Sin leer nada, ¿siempre sabes cuál es el siguiente paso?"**

- ✅ **SÍ → G3 ÉXITO**
- ❌ **NO → Debug específico**

---

## NOTAS DE DEBUG

Si algo falla:

1. **"Los números no están claros"**
   - Check: Markdown headers son visibles
   - Fix: Ajustar tamaño/estilo headers

2. **"Sidebar tiene demasiada información"**
   - Check: ¿project_selector() fue eliminado?
   - Debug: Leer main() sidebar lines 3080-3118

3. **"Decision preview no aparece automático"**
   - Check: Condicional `if capture_title.strip():`
   - Debug: Hay algún error en TaskInput o decision_engine.decide()

4. **"User confunde retomar vs crear"**
   - Check: ¿Hay input arriba en home_view()?
   - Fix: Input debe estar SOLO en new_task_view

5. **"Botón Volver no funciona"**
   - Check: `st.session_state["view"] = "home"` se ejecuta
   - Debug: Revisar session_state en new_task_view línea 2013

---

**FIN DEL CHECKLIST**

Usa este documento para validar que G3 funciona como se diseñó.
