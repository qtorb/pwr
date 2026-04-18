# Guía: 3 Variantes del Header — PWR Home

**Status:** Header-only refinement (nada fuera del header fue tocado)

---

## 📋 Resumen de Variantes

### Variante A — SOBRIA
- PWR fuerte (28px, 900 weight)
- Contexto: "Trabajo estructurado con IA"
- Sin pulso/momentum
- CTA "Crear" limpio a la derecha
- **Sensación:** Minimalista, confiable, sin ruido

### Variante B — MOMENTUM
- PWR fuerte (28px, 900 weight)
- Contexto: "Trabajo estructurado con IA"
- Línea de pulso: "📍 3 resultados recientes"
- CTA "Crear" a la derecha
- **Sensación:** Dinámica, con actividad, razón para volver

### Variante C — INTERMEDIA (CANDIDATA PROBABLE)
- PWR fuerte (28px, 900 weight)
- Contexto + Pulso en UNA línea: "Trabajo con IA • 3 resultados recientes"
- CTA "Crear" integrado a la derecha
- **Sensación:** Equilibrada, limpia, informativa sin ruido

---

## 🔍 Comparación Lado-a-Lado

### Test: "¿Consigue esto en 2 segundos?"

**Sé que estoy en PWR:**
- ✅ A: "PWR" está fuerte, tipografía sólida
- ✅ B: "PWR" está fuerte, tipografía sólida
- ✅ C: "PWR" está fuerte, tipografía sólida

**Entiendo qué tipo de espacio es:**
- ✅ A: "Trabajo estructurado con IA"
- ✅ B: "Trabajo estructurado con IA"
- ✅ C: "Trabajo con IA" (más compacto, igual efecto)

**Tengo una razón para volver:**
- ❌ A: No, sin momentum
- ✅ B: Sí, "3 resultados recientes"
- ✅ C: Sí, "3 resultados recientes" (integrado)

**Veo claramente qué acción puedo hacer:**
- ✅ A: Botón "Crear" visible
- ✅ B: Botón "Crear" visible
- ✅ C: Botón "Crear" visible

---

## 🎬 Cómo Ver las Variantes en Vivo

### Opción 1: Ver en archivo HTML (Offline)

Abre cualquiera de estos archivos en tu navegador:

```
CAPTURA_VARIANTE_A.html
CAPTURA_VARIANTE_B.html
CAPTURA_VARIANTE_C.html
```

Estos replican EXACTAMENTE lo que Streamlit mostraría.

### Opción 2: Ver en Streamlit en Vivo

#### Paso 1: Clonar la app con Variante A

En `app.py`, línea ~2380, cambia:

```python
def render_home_header_with_cta():
    # Cambiar a:
    render_home_header_variant_a()
```

Guarda y Streamlit recargará automáticamente.

#### Paso 2: Captura Variante A

En `http://localhost:8501`, la Home ahora mostrará Variante A. Captura.

#### Paso 3: Cambiar a Variante B

En `app.py`, línea ~2380:

```python
def render_home_header_with_cta():
    # Cambiar a:
    render_home_header_variant_b()
```

Guarda y recarga.

#### Paso 4: Captura Variante B

En `http://localhost:8501`, la Home ahora mostrará Variante B. Captura.

#### Paso 5: Cambiar a Variante C

En `app.py`, línea ~2380:

```python
def render_home_header_with_cta():
    # Cambiar a:
    render_home_header_variant_c()
```

Guarda y recarga.

#### Paso 6: Captura Variante C

En `http://localhost:8501`, la Home ahora mostrará Variante C. Captura.

---

## 📊 Código Exacto de Cada Variante

### Variante A

```python
def render_home_header_variant_a():
    """SOBRIA"""
    col_left, col_right = st.columns([0.75, 0.25])

    with col_left:
        st.markdown(
            "<div style='font-size:28px; font-weight:900; color:#0F172A; letter-spacing:-1px; margin-bottom:6px;'>PWR</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            "<div style='font-size:12px; color:#6B7280; line-height:1.4;'>Trabajo estructurado con IA</div>",
            unsafe_allow_html=True
        )

    with col_right:
        if st.button("Crear", key="header_create_a", use_container_width=True, type="primary"):
            st.session_state["view"] = "new_task"
            st.rerun()

    st.divider()
```

### Variante B

```python
def render_home_header_variant_b():
    """MOMENTUM"""
    count, momentum = get_home_momentum()

    col_left, col_right = st.columns([0.75, 0.25])

    with col_left:
        st.markdown(
            "<div style='font-size:28px; font-weight:900; color:#0F172A; letter-spacing:-1px; margin-bottom:6px;'>PWR</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            "<div style='font-size:12px; color:#6B7280; line-height:1.4;'>Trabajo estructurado con IA</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div style='font-size:11px; color:#9CA3AF; margin-top:4px;'>📍 {momentum}</div>",
            unsafe_allow_html=True
        )

    with col_right:
        if st.button("Crear", key="header_create_b", use_container_width=True, type="primary"):
            st.session_state["view"] = "new_task"
            st.rerun()

    st.divider()
```

### Variante C

```python
def render_home_header_variant_c():
    """INTERMEDIA (CANDIDATA)"""
    count, momentum = get_home_momentum()

    col_left, col_right = st.columns([0.75, 0.25])

    with col_left:
        st.markdown(
            "<div style='font-size:28px; font-weight:900; color:#0F172A; letter-spacing:-1px; margin-bottom:2px;'>PWR</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            "<div style='font-size:11px; color:#6B7280;'>Trabajo con IA <span style='color:#9CA3AF;'>•</span> {}</div>".format(momentum),
            unsafe_allow_html=True
        )

    with col_right:
        if st.button("Crear", key="header_create_c", use_container_width=True, type="primary"):
            st.session_state["view"] = "new_task"
            st.rerun()

    st.divider()
```

---

## ✅ Función Helper: `get_home_momentum()`

```python
def get_home_momentum():
    """
    Calcula una señal útil de actividad para el header.
    Retorna: (count, label) donde label es la frase del pulso.
    """
    with get_conn() as conn:
        recent = conn.execute("""
            SELECT COUNT(*) as cnt FROM tasks
            WHERE datetime(updated_at) >= datetime('now', '-7 days')
            AND llm_output IS NOT NULL AND TRIM(llm_output) != ''
        """).fetchone()

        count = recent['cnt'] if recent else 0

        if count == 0:
            return 0, "Comienza a crear"
        elif count == 1:
            return 1, "1 resultado reciente"
        elif count <= 3:
            return count, f"{count} resultados recientes"
        else:
            return count, f"{count} activos listos"
```

---

## 🔍 Qué NO fue Tocado

**VERIFICADO:**
- ❌ Bloque "Continuar desde aquí" — sin cambios
- ❌ Bloque "Últimos activos" — sin cambios
- ❌ Bloque "Proyectos" — sin cambios
- ❌ Tarjetas y densidad — sin cambios
- ❌ Colores de la app — sin cambios
- ❌ Flujo de navegación — sin cambios
- ❌ `project_view()` — sin cambios
- ❌ `omni_input_view()` — sin cambios
- ❌ `result_view()` — sin cambios

**SOLO CAMBIOS EN HEADER:**
- ✅ `render_home_header_variant_a()` — NUEVA
- ✅ `render_home_header_variant_b()` — NUEVA
- ✅ `render_home_header_variant_c()` — NUEVA
- ✅ `get_home_momentum()` — NUEVA (helper)
- ✅ `render_home_header_with_cta()` — MODIFICADA (solo llama a una variante)

---

## 🎯 Recomendación: Variante C

**Por qué C gana:**

1. **Compacta** — Contexto + Momentum en UNA línea (11px)
2. **Informativa** — Tiene pulso sin ocupar espacio extra
3. **Equilibrada** — Ni minimalista al punto de ser fría (como A) ni ruidosa (como B)
4. **Escalable** — Si hay 0 resultados, dice "Comienza a crear" (útil)
5. **Sensación de producto** — No se ve como beta, se ve como workspace real

---

## 📝 Status Técnico

```
✅ Sintaxis verificada: python -m py_compile app.py
✅ Header-only: nada fuera del header fue tocado
✅ 3 variantes implementadas: A, B, C
✅ Helper `get_home_momentum()` integrado
✅ Variante C seleccionada como candidata final
✅ Sin navegación de app afectada
✅ Sin colores de UI modificados
✅ Sin elementos visuales nuevos fuera del header
```

---

## 🎬 Resultado Final

**Variante C está activa en app.py:**

```
Línea 2392: render_home_header_with_cta() → render_home_header_variant_c()
```

La Home ahora muestra:
- PWR (fuerte)
- "Trabajo con IA • 3 resultados recientes" (contexto + momentum)
- Botón "Crear" (CTA)

**Sensación en 2 segundos:**
- ✅ Sé que estoy en PWR (wordmark fuerte)
- ✅ Entiendo qué es (Trabajo con IA)
- ✅ Tengo razón para volver (3 resultados recientes)
- ✅ Sé qué hacer (botón Crear visible)
