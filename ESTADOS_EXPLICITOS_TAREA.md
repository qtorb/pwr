# ESTADOS EXPLÍCITOS DE TAREA: Solución al problema real

**Objetivo**: Eliminar la pausa de 2 segundos detectada en el test
**Causa**: Usuario no entiende en qué estado está la tarea
**Solución**: Modelo mental claro basado en estado visible

---

## PROBLEMA DIAGNOSTICADO

Usuario ve tarea con resultado pero no sabe:
- ¿Ya está hecha?
- ¿Debo refinarla?
- ¿Está en revisión?

Resultado: Pausa 2 segundos leyendo botones para entender.

**Raíz**: El botón [Ejecutar] no representa el estado real.

---

## ESTADOS POSIBLES DE UNA TAREA

### ESTADO 1: SIN EJECUTAR

**Indicador en BD**:
- `llm_output` = NULL o vacío
- `execution_status` = NULL

**Lo que ve el usuario**:

```
┌────────────────────────────────────┐
│ Análisis de costos operativos      │
│                                    │
│ ⏳ LISTO PARA EJECUTAR            │
│                                    │
│ [⚡ Ejecutar análisis]            │
│                                    │
│ Esta tarea aún no ha sido         │
│ ejecutada. El Router elegirá      │
│ el mejor modo para procesarla.    │
└────────────────────────────────────┘
```

**Modelo mental del usuario**:
> "Esta tarea no está hecha. Debo ejecutarla."

**Botón primario**: [⚡ Ejecutar análisis]

---

### ESTADO 2: PROPUESTA LISTA (Demo mode / Preview)

**Indicador en BD**:
- `execution_status` = "preview"
- Hay `llm_output` (propuesta previa)

**Lo que ve el usuario**:

```
┌────────────────────────────────────┐
│ Análisis de costos operativos      │
│                                    │
│ 📋 PROPUESTA LISTA PARA REVISAR   │
│ (Preview - sin conexión a motor)   │
│                                    │
│ [📋 Revisar propuesta]            │
│                                    │
│ El Router ha analizado la tarea   │
│ y genera una propuesta. Puedes    │
│ revisarla o conectar un motor     │
│ para resultado real.              │
└────────────────────────────────────┘
```

**Modelo mental del usuario**:
> "Hay una propuesta. Necesito revisarla antes de proceder."

**Botón primario**: [📋 Revisar propuesta]

---

### ESTADO 3: RESULTADO GENERADO (Executed)

**Indicador en BD**:
- `execution_status` = "executed"
- Hay `llm_output` (resultado real)

**Lo que ve el usuario**:

```
┌────────────────────────────────────┐
│ Análisis de costos operativos      │
│                                    │
│ ✅ RESULTADO GENERADO             │
│ Hace 3 horas · Confianza: 85%     │
│                                    │
│ [🔄 Refinar resultado]            │
│ [📦 Guardar como activo]          │
│                                    │
│ Este análisis está completo.      │
│ Puedes refinarlo con más análisis │
│ o guardarlo para usar después.    │
└────────────────────────────────────┘
```

**Modelo mental del usuario**:
> "Esto ya está hecho. Puedo refinarlo o guardarlo."

**Botón primario**: [🔄 Refinar resultado]

---

### ESTADO 4: ERROR (Failed)

**Indicador en BD**:
- `execution_status` = "failed"

**Lo que ve el usuario**:

```
┌────────────────────────────────────┐
│ Análisis de costos operativos      │
│                                    │
│ ⚠️ INTENTO FALLIDO                │
│ Error: Proveedor no disponible    │
│                                    │
│ [⚡ Reintentar]                   │
│ [🔧 Cambiar configuración]        │
│                                    │
│ El último intento falló. Puedes   │
│ reintentar o cambiar el modo/     │
│ modelo desde configuración.       │
└────────────────────────────────────┘
```

**Modelo mental del usuario**:
> "Algo falló. Tengo que reintentar."

**Botón primario**: [⚡ Reintentar]

---

## IMPLEMENTACIÓN: CAMBIOS EN project_view()

### Antes (Actual - Problemático):

```python
# Línea 2470 aproximadamente
if st.button("Ejecutar", use_container_width=True, key=f"execute_router_{tid}"):
    # ejecutar lógica
```

### Después (Con estado explícito):

```python
# RENDERIZAR ESTADO EXPLÍCITO
def render_task_state(task, project_name):
    """
    Renderiza el estado explícito de la tarea.
    Usuario entiende inmediatamente en qué fase está.
    """
    output = task.get('llm_output', '')
    status = task.get('execution_status')
    updated_at = task.get('updated_at')

    # ESTADO 1: Sin ejecutar
    if not output or not status:
        st.markdown("### ⏳ LISTO PARA EJECUTAR")
        st.caption("Esta tarea aún no ha sido procesada por el Router.")

        if st.button("⚡ Ejecutar análisis", use_container_width=True, key=f"execute_{task['id']}", type="primary"):
            # Lógica de ejecución
            pass

    # ESTADO 2: Propuesta (preview)
    elif status == "preview":
        st.markdown("### 📋 PROPUESTA LISTA PARA REVISAR")
        st.caption("El Router ha generado una propuesta. Revísala antes de proceder.")

        if st.button("📋 Revisar propuesta", use_container_width=True, key=f"review_{task['id']}", type="primary"):
            # Lógica de revisión
            pass

    # ESTADO 3: Ejecutada
    elif status == "executed":
        time_ago = format_time_ago(updated_at)
        st.markdown(f"### ✅ RESULTADO GENERADO")
        st.caption(f"Generado {time_ago}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refinar resultado", use_container_width=True, key=f"refine_{task['id']}", type="primary"):
                # Lógica de refinamiento
                pass
        with col2:
            if st.button("📦 Guardar como activo", use_container_width=True, key=f"save_{task['id']}"):
                # Lógica de guardado
                pass

    # ESTADO 4: Error
    elif status == "failed":
        st.markdown("### ⚠️ INTENTO FALLIDO")
        st.caption("El último intento no se completó correctamente.")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⚡ Reintentar", use_container_width=True, key=f"retry_{task['id']}", type="primary"):
                # Lógica de reintento
                pass
        with col2:
            if st.button("🔧 Cambiar configuración", use_container_width=True, key=f"config_{task['id']}"):
                # Lógica de config
                pass

# Usar en project_view():
render_task_state(task, project_name)
```

---

## VISUAL COMPARISON: ANTES vs DESPUÉS

### ANTES (Problema)

```
┌────────────────────────────────┐
│ Análisis de costos operativos  │
│                                │
│ [Ejecutar] [Guardar] [Mejorar] │
│                                │
│ CONTENIDO...                   │
│                                │
│ Usuario piensa: "¿Qué hago?"   │
└────────────────────────────────┘
→ Pausa 2 segundos
```

### DESPUÉS (Solución)

```
┌────────────────────────────────┐
│ Análisis de costos operativos  │
│                                │
│ ✅ RESULTADO GENERADO          │
│ Hace 3 horas                   │
│                                │
│ [🔄 Refinar] [📦 Guardar]     │
│                                │
│ CONTENIDO...                   │
│                                │
│ Usuario sabe: "Puedo refinar o │
│ guardar esto"                  │
└────────────────────────────────┘
→ Cero pausa. Acción inmediata.
```

---

## CAMBIOS NECESARIOS EN app.py

### Ubicación: Dentro de project_view(), línea ~2470

**Cambio**:
- ❌ Eliminar: Botón simple [Ejecutar] + [Guardar] + [Mejorar]
- ✅ Agregar: Función `render_task_state()` que muestra estado explícito

**Líneas a modificar**:
1. Línea 2468-2470: Botón [Ejecutar] → Reemplazar con `render_task_state()`
2. Línea 2641-2663: Acciones post-resultado → Integrar en `render_task_state()`

**Total de cambios**: ~50-80 líneas (refactorización de lógica existente)

---

## TEST: Validar que pausa desaparece

### Escenario 1: Tarea sin resultado

**Antes**: Usuario lee "Ejecutar" y piensa si debe hacerlo
**Después**: Lee "⏳ LISTO PARA EJECUTAR" y sabe inmediatamente

Pausa: ❌ 2 seg → ✅ 0 seg

---

### Escenario 2: Tarea con resultado

**Antes**: Usuario ve [Ejecutar], [Guardar], [Mejorar] y no sabe cuál es la acción principal
**Después**: Lee "✅ RESULTADO GENERADO" y ve dos opciones claras: Refinar o Guardar

Pausa: ❌ 2 seg → ✅ 0 seg

---

### Escenario 3: Tarea en propuesta

**Antes**: Usuario no sabe si es una propuesta o un resultado final
**Después**: Lee "📋 PROPUESTA LISTA PARA REVISAR" y sabe exactamente qué hacer

Pausa: ❌ 2-3 seg → ✅ 0 seg

---

## IMPACTO EN HOME V2

**Home V2 sigue siendo correcto.**

Home → project_view ahora tiene:
- ✅ Estado explícito
- ✅ Botones primarios claros
- ✅ Cero confusión
- ✅ Flujo sin fricción

---

## RESUMEN DE CAMBIOS

| Aspecto | Antes | Después | Impacto |
|---------|-------|---------|---------|
| **Usuario ve** | Botones genéricos | Estado explícito | Entiende de inmediato |
| **Modelo mental** | Confuso | Claro | Cero dudas |
| **Botón primario** | Ambiguo | Contextual | Acción obvia |
| **Pausa detectada** | 2 segundos | 0 segundos | Flujo fluido |
| **Cambio de código** | Refactorización | Refactorización | +50-80 líneas |

---

## RECOMENDACIÓN

**Implementar estados explícitos en project_view().**

Esto NO es un cambio de Home V2. Es una mejora necesaria en project_view() para que la experiencia completa (Home → project_view) sea fluida.

**Después de esto**: Home V2 está CERRADA y funcional.

**Prioridad**: Alta (afecta experiencia usuario)

**Esfuerzo**: Bajo-Medio (refactorización, ~2 horas)

**Beneficio**: Elimina completamente la fricción detectada
