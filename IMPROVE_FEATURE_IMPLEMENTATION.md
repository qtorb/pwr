# Implementación: "Mejorar con análisis más profundo"

## 🎯 Objetivo
Transformar el botón "Mejorar resultado" de una función técnica en una **experiencia de mejora** que permita al usuario sentir la diferencia entre análisis rápido (ECO) y análisis profundo (RACING).

---

## 🧩 Arquitectura Implementada

### 1. **Trigger: Click en "✨ Mejorar con análisis más profundo"**
```python
# Línea 1932-1934: Al pulsar el botón
if st.button("✨ Mejorar con análisis más profundo", ...):
    st.session_state[improve_in_progress_key] = True
    st.rerun()
```

### 2. **Ejecución: Spinner + RACING Mode**
```python
# Línea 1937-1990: Flujo de mejora
if st.session_state.get(improve_in_progress_key, False) and not st.session_state.get(improved_result_key):
    # Mostrar progreso visual (3 mensajes)
    # Crear TaskInput con:
    #   - preferred_mode="racing" (fuerza gemini-2.5-pro)
    #   - contexto enriquecido (resultado anterior incluido)
    # Ejecutar y guardar resultado mejorado
    # Hacer rerun para mostrar resultado
```

**Claves de session_state usadas:**
- `improve_in_progress_{tid}` → bool, indica si está mejorando
- `improved_result_{tid}` → string, resultado mejorado
- `improved_trace_{tid}` → dict, metadatos de ejecución mejorada

### 3. **Visualización: Bloque de Resultado Mejorado**
```python
# Línea 2078-2168: Si existe improved_result_key
if st.session_state.get(improved_result_key):
    # Mostrar:
    # - Título "🔵 Resultado mejorado"
    # - Textarea editable (altura 280)
    # - Info: modelo, latencia, costo
    # - 3 botones de acción
```

### 4. **Decisión del Usuario: 3 Opciones**

#### Opción A: "✓ Usar este resultado"
- Reemplaza el resultado original en BD
- Actualiza trace_key con datos de la ejecución mejorada
- Limpia estados de mejora
- Muestra éxito y reinicia

#### Opción B: "↔️ Comparar"
- Muestra mensaje de ayuda
- El usuario puede desplazarse para ver ambos resultados

#### Opción C: "✕ Descartar"
- Rechaza la mejora
- Vuelve al resultado original
- Limpia todos los estados de mejora

---

## 💡 Experiencia del Usuario

### Flujo paso a paso:

1. **Paso 0: Estado inicial**
   - Resultado original visible
   - Botones de acción disponibles

2. **Paso 1: Usuario pulsa "Mejorar"**
   - Desaparece todo excepto spinner
   - 3 mensajes progresivos muestran que está funcionando

3. **Paso 2: Resultado mejorado aparece**
   - Arriba: resultado original (sin cambios)
   - Debajo: línea separadora
   - Debajo: "🔵 Resultado mejorado"
   - Usuario puede editar el mejorado

4. **Paso 3: Usuario elige**
   - Si "Usar": el mejorado reemplaza al original
   - Si "Comparar": mensaje informativo
   - Si "Descartar": vuelve al original

---

## 🔧 Detalles Técnicos

### Enriquecimiento de Contexto
```python
enriched_context = f"{task['context'] or ''}\n\n[RESULTADO ANTERIOR]\n{output}"
```
El contexto incluye el resultado anterior para que el modelo pueda:
- Entender qué se hizo antes
- Mejorar basándose en ese punto de partida
- No repetir lo mismo

### Forzar RACING Mode
```python
improved_task_input = TaskInput(
    ...
    preferred_mode="racing"  # ← El DecisionEngine respeta esto
)
```
El DecisionEngine detecta `preferred_mode` y lo usa directamente sin cálculos.

### Guardado de Datos
Cuando se elige "Usar este resultado":
- Se llama a `save_execution_result()` con el nuevo output
- Se actualiza `router_summary` con detalles de la mejora
- Se actualiza `llm_output` en BD
- El trace_key se actualiza para mostrar datos correctos

---

## ✅ Validación de Comportamiento

**Criterio de éxito (usuario piensa):**
- ✅ "Vale, esto sí es mejor" → El flujo funcionó
- ❌ "No sé qué ha pasado" → Hay que revisar UX

**No implementado:**
- ❌ NO sobrescribe automáticamente (usuario decide)
- ❌ NO elimina resultado original (ambos visibles)
- ✅ Permite comparación fácil (desplazarse)
- ✅ Usuario decide (3 botones claros)

---

## 🚀 Posicionamiento

Este botón es **el primer paso hacia monetización**:
- Demuestra valor diferencial (ECO vs RACING)
- El usuario experimenta mejora real
- Justifica el costo de usar modelo más potente
- Preparar para: "Análisis premium" (versión pago)

---

## 📝 Notas de Implementación

1. Las claves de session_state se definen al inicio de la sección de acciones (línea 1915-1919)
2. El flujo de mejora se ejecuta UNA SOLA VEZ (guardas: `improve_in_progress_key AND NOT improved_result_key`)
3. El resultado mejorado es editable (user puede refinar antes de usar)
4. Los botones de acción mantienen toda la información necesaria para guardar

---

## 📍 Ubicación en Código

- **Definición de claves**: `app.py` línea 1915-1919
- **Botón "Mejorar"**: `app.py` línea 1931-1934
- **Flujo de mejora**: `app.py` línea 1937-1990
- **Visualización mejorada**: `app.py` línea 2078-2168
