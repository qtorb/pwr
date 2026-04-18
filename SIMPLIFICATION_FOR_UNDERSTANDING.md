# Simplificación Radical: Hacer que PWR se Entienda

## 🎯 Objetivo
El usuario entra y en **3 segundos entiende qué hacer**.

---

## ❌ Problema Anterior
La pantalla transmitía:
- "Tengo que elegir cosas"
- "Hay varios inputs"
- "Parece un configurador"

**Resultado**: El usuario no entiende PWR y se va.

---

## ✅ Solución Implementada

### Principio Clave
**El usuario SOLO escribe. El sistema decide TODO lo demás.**

### Cambios en HOME (Estado con Actividad)

#### Antes:
```
[Selector de proyecto] ← Confusión: ¿cuál elijo?
[Input] [Checkbox "Opciones"] [Botón]
[Opciones avanzadas ocultas pero disponibles] ← Parece complejo
```

#### Después:
```
Trabajando en: [Proyecto automático]
────────────────────────────────
## ¿Qué necesitas hacer ahora?
[UN ÚNICO INPUT]
"El sistema elegirá automáticamente..."
[Expandible cerrado] Añadir contexto
[Botón Ejecutar]
```

### Cambios en PROJECT_VIEW (Sidebar)

#### Antes:
```
[Caption proyecto]
[Input con label]
[Spacing]
[Expander opciones]
  [Selector tipo]
  [Text area descripción]
  [Text area contexto]
  [File uploader]
[Botón]
```

#### Después:
```
Trabajando en: [Proyecto]
## ¿Qué necesitas hacer ahora?
[UN ÚNICO INPUT]
"El sistema elegirá..."
[Expandible] Añadir contexto
[Botón]
```

---

## 📝 Cambios Técnicos

### 1. HOME: Eliminar Selector de Proyecto
```python
# ANTES
selected_project_name = st.selectbox("Proyecto", project_names)

# DESPUÉS
default_project = projects[0]  # Automático
st.caption(f"Trabajando en: **{default_project['name']}**")
```

### 2. HOME: Eliminar Checkbox "Opciones"
```python
# ANTES
show_advanced = st.checkbox("Opciones", ...)
if show_advanced:
    # mostrar campos adicionales

# DESPUÉS
# ❌ Eliminado completamente
# TODO es automático
```

### 3. HOME: Simplificar Input
```python
# ANTES
st.text_input("Tarea", ...)

# DESPUÉS
st.markdown("## ¿Qué necesitas hacer ahora?")
st.text_input("", ...)  # Label vacío
```

### 4. HOME: Añadir Mensaje Clave
```python
st.caption("El sistema elegirá automáticamente la mejor forma de ejecutar la tarea")
```

### 5. HOME: Contexto Progresivo
```python
with st.expander("Añadir contexto (opcional)"):
    st.text_area("", ...)  # Cerrado por defecto
```

### 6. PROJECT_VIEW: Eliminar Opciones Avanzadas
```python
# ANTES
with st.expander("⚙️ Opciones avanzadas"):
    task_type = st.selectbox(...)
    description = st.text_area(...)
    context = st.text_area(...)

# DESPUÉS
# ❌ Eliminado
# Contexto SOLO si usuario abre expander
```

### 7. PROJECT_VIEW: Un Input, Un Mensaje, Un Botón
```python
st.markdown("## ¿Qué necesitas hacer ahora?")
title = st.text_input("", ...)
st.caption("El sistema elegirá automáticamente...")
with st.expander("Añadir contexto (opcional)"):
    context = st.text_area("", ...)
st.button("Ejecutar tarea", disabled=not title.strip())
```

---

## 🧠 Experiencia del Usuario

### Antes (Confusión)
```
1. Entra en PWR
2. Ve selector de proyecto → ¿Cuál elijo?
3. Ve checkbox "Opciones" → ¿Qué pasa si lo activo?
4. Si activa, ve más campos → Parece un formulario
5. No entiende qué es PWR
6. Se va
```

### Después (Claridad)
```
1. Entra en PWR
2. Lee: "¿Qué necesitas hacer ahora?"
3. Ve un input limpio
4. Lee: "El sistema elegirá automáticamente..."
5. Entiende: "Ah, esto es como ChatGPT pero inteligente"
6. Escribe su tarea
7. Pulsa ejecutar
✅ FIN
```

---

## ✅ Validación

**Estructura FINAL:**

HOME (estado con actividad):
```
Título: "Portable Work Router"
Caption: "Retoma tu trabajo..."
Caption: "Trabajando en: {proyecto}"
Markdown: "## ¿Qué necesitas hacer ahora?"
Input: UN ÚNICO INPUT
Caption: "El sistema elegirá..."
Expander: "Añadir contexto (opcional)"
Botón: "Ejecutar tarea"
────────────────────────────
Continuar trabajo (sección)
Proyectos (sección)
```

PROJECT_VIEW (sidebar):
```
Caption: "Trabajando en: {proyecto}"
Markdown: "## ¿Qué necesitas hacer ahora?"
Input: UN ÚNICO INPUT
Caption: "El sistema elegirá..."
Expander: "Añadir contexto (opcional)"
Botón: "Ejecutar tarea"
────────────────────────────
Tareas activas (sección)
```

**Criterios cumplidos:**
- ✅ Solo hay UN input visible (el principal)
- ✅ El usuario no tiene que decidir nada antes de escribir
- ✅ Todo lo demás es opcional (expander cerrado) o invisible
- ✅ En 3 segundos entiende qué hacer

---

## 🚀 Siguiente Fase

Con esta simplificación como base:
1. **Probar flujo completo** — Usuario escribe y ejecuta
2. **Potenciar post-ejecución** — Crear el "WOW moment"
3. **Validar comprensión** — El usuario ahora entiende PWR

---

## 📊 Resumen de Cambios

| Elemento | Antes | Después |
|----------|--------|---------|
| Selector proyecto | Visible, obligatorio | Automático, caption discreta |
| Input principal | Con label | Label vacío, markdown arriba |
| Opciones avanzadas | Visible/oculto por checkbox | Eliminado |
| Contexto | En opciones avanzadas | Expander cerrado, opcional |
| Tipo/descripción | Inputs visibles | Automático |
| Mensaje | Genérico | "El sistema elegirá..." |
| Complejidad percibida | Alta (formulario) | Baja (una acción) |

