# HOME V2 - VERSIÓN AUSTERA

**Status**: ✅ Implementada - Solo Streamlit nativo, sin HTML crudo

---

## Filosofía de Cambio

La versión anterior tenía:
- ❌ HTML crudo renderizado (feo)
- ❌ Demasiados componentes duplicados
- ❌ 4 bloques confusos sin jerarquía clara
- ❌ Aire muerto excesivo

La nueva versión tiene:
- ✅ Solo componentes Streamlit nativos
- ✅ 3 funciones claramente definidas
- ✅ Línea de captura única y limpia
- ✅ Densidad visual adecuada

---

## Las 3 Funciones

### 1️⃣ CAPTURAR TAREA (Línea única)
```
┌──────────────┬─────────────────────────────┬───────────┬──────────┐
│  Proyecto ▼  │  Pensar, escribir, ...      │ Opciones ☐│ Capturar │
└──────────────┴─────────────────────────────┴───────────┴──────────┘

Si activas "Opciones" aparecen 3 campos en una fila:
┌──────────────┬──────────────┬──────────────┐
│ Tipo (select)│ Descripción  │ Contexto     │
└──────────────┴──────────────┴──────────────┘
```

**Componentes:**
- Selector de proyecto (pequeño, izquierda)
- Input principal (grande, centro)
- Checkbox "Opciones" (discreto)
- Botón "Capturar" (CTA principal)
- Si activa opciones: 3 campos colapsados que aparecen

**Comportamiento:**
- Botón deshabilitado hasta que hay texto + proyecto
- Success message cuando captura
- Redirecciona al proyecto

---

### 2️⃣ CONTINUAR TRABAJO (Lista compacta)
```
Principal · PWR · Pensar
Explicar algoritmo de búsqueda
Sonnet · Hace 1 hora           [→]

─────────────────────────────────────

— · PWR · Escribir
Documentar endpoints API
ECO · Ayer                     [→]

─────────────────────────────────────
```

**Componentes:**
- Por tarea: nombre del proyecto, tipo, modelo, tiempo
- Título de la tarea
- Botón → (compacto, abre tarea en proyecto)
- Primera tarea marcada como "Principal"
- Sin HTML, solo filas de Streamlit

**Comportamiento:**
- Máximo 3 tareas
- Empty state: caption simple
- Al clickear → abre proyecto + tarea

---

### 3️⃣ PROYECTOS RECIENTES (Tarjetas simples)
```
PWR
3 tareas · Última: hace 1h    [Abrir]  [⭐]

─────────────────────────────────────

RosmarOps
5 tareas · Última: ayer       [Abrir]  [☆]

─────────────────────────────────────

[➕ Crear nuevo proyecto]
```

**Componentes:**
- Nombre proyecto (bold)
- Metadata: task count + last activity
- [Abrir] botón (CTA principal, ancho)
- ⭐/☆ icono toggle (discreto, derecha)
- "Crear nuevo proyecto" button (secundario, abajo)

**Comportamiento:**
- Máximo 2 proyectos mostrados
- Empty state: caption + botón crear
- ⭐ toggle como favorito
- [Abrir] → abre proyecto
- Botón crear abre form en expander

---

## Cambios Técnicos

### Eliminado
- ❌ Todo renderizado HTML crudo (`<div>`, `<button onclick>`, etc.)
- ❌ JavaScript
- ❌ Bloques vacíos innecesarios
- ❌ CSS classes `.home-*` excesivas

### Mantenido
- ✅ Helper functions: `get_recent_executed_tasks()`, `get_projects_with_activity()`, `format_time_ago()`
- ✅ Session state para modal
- ✅ Integración con router (continuación de tareas)

### CSS Requerido (Mínimo)
- Eliminar todas las classes `.home-*` complejas
- Mantener solo:
  - `.stDivider` para separadores
  - Estilos generales existentes
  - Si necesario: pequeños ajustes de spacing

---

## Estructura Código

```python
def home_view():
    st.title("Portable Work Router")
    st.caption("Retoma tu trabajo • captura tareas • usa el mejor modelo")

    # Sección 1: Captura (línea única + opciones colapsadas)
    cap_cols = st.columns([0.8, 2.5, 0.8, 0.8])
    # ... input + selector + opciones checkbox ...

    st.divider()

    # Sección 2: Continuar trabajo (lista simple)
    recent_tasks = get_recent_executed_tasks(limit=3)
    # ... loop sobre tareas con botones → ...

    st.divider()

    # Sección 3: Proyectos (tarjetas simples)
    projects_with_activity = get_projects_with_activity()
    # ... loop sobre proyectos con [Abrir] y ⭐ ...

    # Modal: Crear proyecto
    if st.session_state.get("show_create_project"):
        # ... form con st.form() ...
```

---

## Flow Usuario

1. **Aterriza en home**: Ve captura, trabajos recientes, proyectos
2. **Captura tarea**:
   - Selecciona proyecto
   - Escribe tarea
   - [Capturar]
   - ✓ Success → Redirecciona a proyecto
3. **Continúa trabajo**:
   - Ve listado de tareas recientes
   - Clickea →
   - Abre proyecto + tarea
4. **Abre proyecto reciente**:
   - Clickea [Abrir]
   - Abre proyecto
5. **Crea proyecto**:
   - [➕ Crear nuevo proyecto]
   - Form expande
   - Llenar y submit
   - Redirecciona a proyecto

---

## Visual Qualities

✓ **Claridad**: Solo 3 acciones visibles
✓ **Densidad**: Sin aire muerto, información útil
✓ **Jerarquía**: Captura > Continuar > Proyectos
✓ **Austeridad**: Streamlit puro, no HTML crudo
✓ **Funcionalidad**: Todos los botones son CTAs reales (no alerts)

---

## Próximos Pasos (Si necesario)

- Ajustar colores de botones si es necesario
- Refinar spacing en columnas si se siente apretado
- Considerar agregar ícono a "Continuar" (flecha)
- Si falta peso visual, agregar subtle divider entre secciones

---

**Versión 2 lista para testing en `http://localhost:8501`**
