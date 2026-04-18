# BLOQUE B: Microplan de UI Restructuring (Acotado)

**Objetivo:** Mejorar jerarquía visual. Usuario ve propuesta, no tripas.
**Scope:** SOLO presentación. Sin cambios de lógica.
**Alcance:** Acotado (4 cambios discretos)

---

## 1. Archivos a Tocar

### Modificar (existentes)
```
app.py (PROJECT_VIEW, sección post-ejecución)
  - Línea ~2230: Expandible trazabilidad
  - Línea ~2290: Decision display
  - Línea ~2010: Warning/error display
  - Línea ~2120: Estructura general de result blocks
```

### NO tocar
```
router/ (ningún archivo)
app.py (HOME_VIEW, fallback logic, execution logic)
init_db(), save_execution_result(), generate_demo_proposal(), display_demo_mode_panel()
```

---

## 2. Qué Cambia Visualmente

### Cambio 1: Trazabilidad Colapsada por Defecto
**Hoy (línea ~2230):**
```python
with st.expander("🔍 Trazabilidad", expanded=False):  # Ya está colapsada
    st.write(f"**Estado:** {trace['status'].upper()}")
    ...
```

**Resultado visual actual:**
```
[Ficha del proyecto ▼]
[Prompt sugerido ▼]
[🔍 Trazabilidad ▼]
[🎯 Activos relacionados ▼]
```

**Cambio:**
- Mantener `expanded=False` (ya estaba)
- PERO agregar nota visual: "ℹ️ Detalles técnicos colapsados" en el header del expander

**Nuevo visual:**
```
[Ficha del proyecto ▼]
[Prompt sugerido ▼]
[🔍 Trazabilidad ▼ ℹ️ detalles técnicos]
[🎯 Activos relacionados ▼]
```

**Líneas a cambiar:** 1 (agregar label descriptivo)

---

### Cambio 2: Mejorar Jerarquía Visual Resultado → Decisión
**Hoy:**
```
[RESULTADO text_area 280px]
[Línea de continuidad]
[4 botones]
[Ficha del proyecto]
[Prompt]
[Trazabilidad]
[Activos]
----- (divider)
[Decision display]   ← al final, después de todo
```

**Problema:** Decision display compite con expandibles por espacio/atención.

**Cambio:**
1. Mover `st.write("")` y `st.markdown("---")` ANTES de expandibles (hoy está después)
2. Resultado (280px) → Botones → Decision display JUNTOS (como bloque coherente)
3. Expandibles DESPUÉS (section separada)

**Nuevo visual:**
```
[RESULTADO text_area 280px]
[Línea de continuidad]
[4 botones]
[Mejorar flujo / Guardar flujo / etc]
---
[Decision display] ← prominente, antes de expandibles
---
[Expandibles colapsados ▼]
  [Ficha proyecto]
  [Prompt]
  [Trazabilidad ℹ️]
  [Activos]
```

**Líneas a cambiar:** ~5 (reorganizar dividers, st.write(""))

---

### Cambio 3: Mejorar Presentation de Warnings/Errores Reales
**Hoy (línea ~1930):**
```python
else:  # Error real (no fallback)
    st.warning(f"⚠️ Error de ejecución: {result.error.message}")
```

**Visual actual:**
```
⚠️ Error de ejecución: [error mensaje técnico]
```

**Cambio:**
- Mensajes de error menos técnicos
- Agregar contexto útil (qué significa, qué hacer)
- Estructura clara: Problema → Explicación → Acción sugerida

**Nuevo visual:**
```
⚠️ Error durante ejecución

Problema: No se pudo conectar con el proveedor.
Motivo: [error code + mensaje simplificado]

Opciones:
• Reintentar (el servidor puede estar saturado)
• Revisar tu conexión a internet
• Si el problema persiste, intenta en 5 minutos
```

**Líneas a cambiar:** ~10 (mejorar mensajes + estructura)

---

### Cambio 4: Detalles Técnicos en Panel Discreto (Futuro)
**Hoy:** Detalles técnicos dentro del expandible Trazabilidad

**Para futuro (no implementar en B):**
- Crear expander "🔧 Detalles técnicos" separado
- Contendrá: latencia, coste, reasoning path completo
- Colapsado por defecto
- Discreto, no interfiere con propuesta

**En B:** Solo preparar la estructura (mover contenido de Trazabilidad para que sea movible después)

**Líneas a cambiar:** 0 ahora (preparación conceptual)

---

## 3. Qué NO Cambia

```
✓ Fallback logic (generate_demo_proposal, display_demo_mode_panel)
✓ Ejecución (execution_service.execute)
✓ Estados persistidos (executed, preview, failed)
✓ ModelCatalog
✓ HOME view
✓ Decisión del Router
✓ Botones de acciones (Guardar, Mejorar, etc)
✓ Flujos secundarios (Mejorar, Guardar, Comparar)
```

---

## 4. Riesgos y Efectos Secundarios

### Riesgo 1: Reorganizar dividers rompe layout
**Impacto:** BAJO
**Mitigación:** Pruebar incrementalmente, mantener st.write("") para espaciado

### Riesgo 2: Cambiar orden de expandibles confunde usuarios
**Impacto:** BAJO (ya están colapsados, orden es cosmético)
**Mitigación:** Mantener orden lógico (Ficha → Prompt → Detalles → Activos)

### Riesgo 3: Mejorar mensajes de error introduce copy subjetivo
**Impacto:** BAJO
**Mitigación:** Copy debe ser claro y accionable, no técnico ni marketing

### Riesgo 4: Mover decision display puede afectar visual si hay mucho contenido
**Impacto:** MUY BAJO (decision display es compacto, ~100px)
**Mitigación:** Probar con tarea real larga

---

## 5. Compatibilidad con Model Radar

### ¿Interfiere B con Model Radar?
**NO.** B solo toca presentación.

### ¿Ayuda B a preparar Model Radar?
**Sí, indirectamente:**
- Separar detalles técnicos en expander discreto
- Permite que iteración D agregue "Detalles técnicos" sin tocar propuesta central
- Decisión display prominente es agnóstica a fuente (hoy: mode_registry, mañana: BD)

### ¿Hay algo que B deba evitar?
**Sí:**
- ❌ NO hardcodear más detalles técnicos en UI
- ❌ NO acoplar decisión display a estructura de trace (mantener agnóstica)
- ✅ SÍ preparar estructura para que expander pueda recibir datos de model_catalog futura

---

## 6. Criterio de Éxito de B

### Visualmente
- [ ] Resultado (280px) está prominente arriba
- [ ] 4 botones están claramente debajo del resultado
- [ ] Decision display está arriba de expandibles
- [ ] Expandibles colapsados, sin competir con propuesta central
- [ ] Warnings/errores son claros y accionables

### Funcionalmente
- [ ] Ningún cambio de lógica
- [ ] Estados persistidos sin cambios
- [ ] Fallback sigue funcionando igual
- [ ] Botones siguen siendo funcionales
- [ ] Sin regresión en otros flujos

### Técnicamente
- [ ] Código compila
- [ ] Componentes Streamlit sin cambios de tipo
- [ ] Save/load sigue igual
- [ ] Session state sin impacto

---

## Cambios Línea por Línea (Estimado)

### Resumen de cambios
```
app.py PROJECT_VIEW:
  - ~5 líneas: Reorganizar dividers (trazabilidad después de result)
  - ~10 líneas: Mejorar mensajes de error (st.warning)
  - ~1 línea: Agregar label a trazabilidad expander
  - ~3 líneas: Agregar espaciado entre secciones
  -----
  Total: ~19 líneas modificadas
  Líneas afectadas: 2010, 2120-2150, 2230-2290
```

---

## No Tocar (Scope Fence)

```
❌ HOME view (ya está bien)
❌ Fallback logic (bloque A)
❌ Ejecución (router)
❌ Settings UI (futuro)
❌ Features nuevas (modelo demo, mejorar, etc)
❌ Refactor arquitectura (B es cosmético)
```

---

## Orden de Cambios (Secuencial)

**Paso 1:** Reorganizar orden de expandibles (trazabilidad después de result)
→ Verificar que layout no rompe

**Paso 2:** Agregar label descriptivo a trazabilidad
→ Verificar visual

**Paso 3:** Mejorar mensajes de warning (error real)
→ Verificar copy

**Paso 4:** Revisar jerarquía general
→ Verificar que decisión display está bien posicionada

---

## Resumen del Microplan

| Aspecto | Descripción |
|---------|-------------|
| **Scope** | SOLO UI, NO lógica |
| **Cambios** | 4 discretos (trazabilidad label, jerarquía visual, warnings, preparación detalles) |
| **Líneas** | ~19 cambios en app.py |
| **Archivos** | 1 (app.py) |
| **Riesgo** | BAJO |
| **Compatibilidad Model Radar** | SÍ, cero interferencia |
| **Complejidad** | BAJA (reorganizar + mejorar copy) |
| **Tiempo estimado** | 1-2 horas |

---

## Validación Previa

Antes de implementar, revisar:
- [ ] Esto no cambia fallback logic
- [ ] Esto no toca ModelCatalog
- [ ] Esto no abre Settings
- [ ] Esto no agrega features
- [ ] Esto NO complica Model Radar

**Todas las casillas:** ✓ Sí

---

## Listo para Implementación

Este microplan es:
- ✅ Acotado
- ✅ Específico
- ✅ Bajo riesgo
- ✅ Compatible Model Radar
- ✅ Cumple scope permitido

**Siguiente:** Esperar aprobación de Albert para implementar.
