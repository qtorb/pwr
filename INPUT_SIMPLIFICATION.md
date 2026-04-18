# Simplificación Radical del Input

## 🎯 Transformación: De Formulario a ChatGPT

### Principio Clave
**Si el usuario tiene que decidir algo ANTES de escribir → Es un bug**

---

## ❌ Problemas Eliminados

### 1. CONTEXT BAR (HTML crudo)
- **Antes**: Mostraba "Estado del Proyecto" con 3 items en HTML
- **Después**: Simple caption: `"Trabajando en: {proyecto}"`

### 2. COMMAND BAR (HTML crudo)
- **Antes**: Etiqueta decorativa "Capturar Tarea"
- **Después**: Eliminado (el input habla por sí solo)

### 3. Selector de Tipo
- **Antes**: Expander con `st.selectbox("Tipo", TIPOS_TAREA)`
- **Después**: ❌ Eliminado completamente
- **Por qué**: El Router decide el tipo automáticamente

### 4. Campos de Descripción/Contexto Visibles
- **Antes**: Expander con campos siempre visibles
- **Después**: PROGRESIVO: Expander "Añadir contexto" (cerrado por defecto)

### 5. File Uploader Manual
- **Antes**: Usuario seleccionaba archivos manualmente
- **Después**: ❌ Eliminado (se añadirá automático después)

---

## ✅ Nueva Estructura

### Sidebar Now:

```
Trabajando en: Herramientas del MMDD
────────────────────────────────────

¿Qué necesitas hacer ahora?
[input: Ej: resume este documento...]

────────────────────────────────────
[Expandible cerrado] Añadir contexto (opcional)
  └─ Notas adicionales [textarea]

────────────────────────────────────
[Botón] Ejecutar tarea

────────────────────────────────────
Tareas activas (5)
  [lista de tareas...]
```

---

## 🔄 Cambios Técnicos

### 1. Proyecto como Hint (No Selector)
```python
st.caption(f"Trabajando en: **{project['name']}**")
```
- Solo INFORMACIÓN, no decisión
- Usa proyecto activo automáticamente

### 2. Input Protagonista
```python
st.text_input(
    "¿Qué necesitas hacer ahora?",
    placeholder="Ej: resume este documento • escribe un email • analiza un excel",
)
```
- Label claro
- Placeholder inspirador (ejemplos reales)
- NO label_visibility="collapsed"

### 3. Contexto Progresivo
```python
with st.expander("Añadir contexto (opcional)", expanded=False):
    st.text_area("Notas adicionales", height=60)
```
- **Cerrado por defecto** → El usuario NO ve complejidad
- **Opcional** → Etiqueta clara
- **Accesible** → Si usuario necesita, está ahí

### 4. Botón Claro
```python
st.button("Ejecutar tarea", use_container_width=True)
```
- Nombre: "Ejecutar tarea" (no "Crear")
- Sin botones secundarios en esta zona

### 5. Tipo Auto-Detectado
```python
task_type = TIPOS_TAREA[0]  # Default
# El Router decide el tipo real basándose en el contenido
```
- El usuario NO selecciona tipo
- El Router lo detecta automáticamente

---

## 🧠 Experiencia del Usuario

### Antes (Fricción)
```
1. Veo selector de tipo → ¿Cuál elijo?
2. Veo "Descripción" → ¿Es obligatorio?
3. Veo "Contexto" → ¿Qué va aquí?
4. Veo file_uploader → ¿Cargo archivos?
5. Finalmente escribo algo
→ Sensación: "Esto es como un formulario"
```

### Después (Fluidez)
```
1. Leo: "¿Qué necesitas hacer ahora?"
2. Escribo mi intención
3. Si necesito añadir notas → Expander
4. Pulso "Ejecutar"
→ Sensación: "Esto es como ChatGPT"
```

---

## ✅ Validación

**Cambios realizados:**
- ✅ Eliminado HTML crudo (CONTEXT BAR, COMMAND BAR)
- ✅ Eliminado selector de tipo
- ✅ Eliminado file_uploader manual
- ✅ Input como protagonista único
- ✅ Contexto progresivo (opcional, cerrado)
- ✅ Proyecto como hint

**Sintaxis:**
- ✅ Código compila sin errores

**UX:**
- ✅ Usuario escribe sin pensar
- ✅ No hay decisiones previas
- ✅ Todo lo demás es opcional o invisible

---

## 🚀 Próximos Pasos

1. **Probar flujo completo** — Usuario escribe y ejecuta
2. **Potenciar post-ejecución** — WOW moment, versiones, etc.
3. **Automáticos** — Carga de archivos automática, tipos detectados

---

## 📍 Cambios en Código

**Archivo**: `app.py` (sidebar)

**Líneas eliminadas:**
- CONTEXT BAR HTML (1526-1548)
- COMMAND BAR HTML (1551-1558)
- Opciones avanzadas expander (1573-1581)
- File uploader (1578)

**Líneas añadidas:**
- Caption proyecto (1 línea)
- Input "¿Qué necesitas hacer ahora?" (renovado)
- Expander "Añadir contexto" (cerrado por defecto)

**Total de cambios**: Simplificación radical. Mismo flujo, menos fricción.
