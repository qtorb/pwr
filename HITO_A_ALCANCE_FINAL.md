# HITO A - ALCANCE FINAL (AJUSTADO)

## 1. ALCANCE FINAL

Visible new flow sin refactor de arquitectura interna.

- ✅ Eliminar sidebar
- ✅ Header mínimo: PWR + Breadcrumb
- ✅ Home claro: una acción principal (Nueva Tarea)
- ✅ Nueva Tarea fullscreen
- ✅ Propuesta como estado con estructura fija (Modo | Modelo | Por qué)

**Restricción**: Cambios en app.py. Máximo 1-2 helpers. Sin modularización masiva.

---

## 2. FICHEROS QUE TOCO REALMENTE

**Tocar:**
- `pwr/app.py` — Eliminar sidebar, añadir header render inline, estructura de estados

**Crear mínimo:**
- `pwr/components/header_render.py` — Helper pequeño (10-20 lineas): render breadcrumb + logo
- O directamente inline en app.py si es < 30 lineas

**Dejar intacto:**
- `pwr/router/` — Sin tocar
- `pwr/database.py` — Sin tocar
- Lógica de propuestas/ejecución — Sin tocar

---

## 3. QUÉ DEJA FUERA

- ❌ No refactorizar a `pages/home.py`, `pages/new_task.py`, etc.
- ❌ No crear componentes grandes de propuesta
- ❌ No cambiar estructura de DB
- ❌ No implementar proyecto.open() funcional (hardcodear lista)
- ❌ No quitar/cambiar lado de propuestas reales (Router decide después)

---

## 4. ORDEN DE EJECUCIÓN

**Paso 1**: Eliminar sidebar de app.py (5 minutos)
- Remover `with st.sidebar:`
- Remover radio button de navegación

**Paso 2**: Crear header inline en app.py (15 minutos)
```
st.markdown("PWR")  # Logo mínimo
st.caption(breadcrumb_text)  # Breadcrumb: "PWR > Proyecto > Tarea > [Estado]"
```

**Paso 3**: Estructura de estados en app.py (30 minutos)
- Home: Mostrar proyectos (hardcodeado o query simple) + input Nueva Tarea
- Nueva Tarea: Input title + description, botón "Ver propuesta"
- Propuesta: Mostrar bloque (Modo ECO | Modelo Flash Lite | Por qué breve)

**Paso 4**: Navegación entre estados (20 minutos)
- Home → Nueva Tarea (click botón "Crear")
- Nueva Tarea → Propuesta (click "Ver propuesta")
- Propuesta → Home (click "Cancelar")

**Paso 5**: Validación manual (20 minutos)
- Flujo completo sin sidebar
- Breadcrumb se actualiza
- Botones funcionan

**Total**: ~1.5 horas de código

---

## VALIDACIÓN POST-HITO A

**Usuario abre app**:
1. ¿Ve Home sin sidebar? ✅
2. ¿Toca "Nueva tarea"? ✅
3. ¿Llena titulo + descripción? ✅
4. ¿Toca "Ver propuesta"? ✅
5. ¿Ve propuesta con Modo | Modelo | Por qué? ✅
6. ¿Breadcrumb actualiza en cada paso? ✅

Si los 6 pasan: Hito A listo. Procede a Hito B (Router real).

---

**Status**: Autorizado a codificar.

*Listo para comenzar ahora.*
