# E1 MICROPLAN v2: Snapshot Layer + Vista Streamlit

**Fecha**: 2026-04-17
**Bloque**: E1 (Catálogo vivo snapshot + visualización)
**Filosofía**: Arquitectura disciplinada, snapshot reutilizable, Streamlit puro.

---

## DECISIÓN ARQUITECTÓNICA

### Rechazado
- ❌ Flask paralelo + threading (complejidad innecesaria)
- ❌ Infraestructura web adicional

### Adoptado
- ✅ **Snapshot Layer**: Función central `build_radar_snapshot(internal=False) -> dict`
- ✅ **Vista Streamlit**: Página/vista que consume snapshot
- ✅ **Diseño reutilizable**: Preparada para export JSON + futura API (sin acoplamientos)

---

## 1. ARCHIVOS A TOCAR

### Archivos Modificados

| Archivo | Cambio | Ubicación | Justificación |
|---------|--------|-----------|---------------|
| **router/model_catalog.py** | Refactor: `export_public_catalog()` → función pública standalone | Línea ~260+ | Snapshot layer es responsabilidad de catálogo |
| **app.py** | Agregar función `build_radar_snapshot(internal=False)` | Línea ~2450+ | Wrapper que instancia ModelCatalog + llama export |
| **app.py** | Agregar vista `radar_view()` con Streamlit UI | Línea ~2470+ | Renderiza snapshot en interfaz |
| **app.py** | Modificar `main()` para routing a `radar_view()` | Línea ~2500+ | Switch tipo: si path == "radar" → radar_view() |

### Archivos Creados

| Archivo | Propósito |
|---------|-----------|
| **E1_SNAPSHOT_TEST.py** | Test suite para validación de snapshot |

### Archivos NO tocados

- DecisionEngine, ExecutionService, domain.py — Intactos
- Lógica de ejecución — Sin cambios

---

## 2. FUNCIÓN SNAPSHOT LAYER

### Definición

```python
# En router/model_catalog.py (método público que ya existe)
def export_public_catalog(self, include_internal: bool = False) -> dict:
    """
    Exporta catálogo como snapshot JSON para /radar.
    [Ya implementado en E0]
    """
    # ... retorna dict con providers, modes, summary
```

### Wrapper en app.py

```python
def build_radar_snapshot(internal: bool = False) -> dict:
    """
    Construye snapshot del catálogo vivo (E1a).

    Responsabilidades:
    - Conectar a BD
    - Instanciar ModelCatalog
    - Llamar export_public_catalog(include_internal=internal)
    - Envolver con metadata

    Args:
        internal: Si False (default), oculta is_internal=1
                  Si True, incluye modelos de test/debug

    Returns:
        {
            "status": "ok|error",
            "radar": {
                "providers": {...},
                "modes": {...},
                "summary": {...}
            },
            "metadata": {
                "generated_at": ISO8601,
                "radar_version": "1.0",
                "catalog_source": "model_catalog BD",
                "framing": "live catalog snapshot (not historical observatory)",
                "note": "Mode is transitional bridge in this phase"
            }
        }

    NOTA: Esta snapshot es REUTILIZABLE para:
    - render en Streamlit (E1b)
    - export a JSON file (E2+)
    - futura API REST /api/radar (E3+)
    - dashboards externos (E3+)
    """
    try:
        with get_conn() as conn:
            catalog = ModelCatalog(conn)
            radar_data = catalog.export_public_catalog(include_internal=internal)

        return {
            "status": "ok",
            "radar": radar_data,
            "metadata": {
                "generated_at": now_iso(),
                "radar_version": "1.0",
                "catalog_source": "model_catalog BD",
                "framing": "live catalog snapshot – NOT observatorio histórico, NOT benchmarking, NOT health monitor, NOT adaptive scoring",
                "note": "Mode = temporal bridge to router_policy table (future)",
                "include_internal": internal
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "metadata": {
                "generated_at": now_iso(),
                "radar_version": "1.0"
            }
        }
```

### Propiedades de Snapshot

| Propiedad | Valor | Razón |
|-----------|-------|-------|
| **Determinístico** | Mismo input → mismo output | Cacheeable, predecible |
| **Reutilizable** | Mismo objeto sirve para múltiples usos | Evita múltiples lecturas de BD |
| **Versionado** | `radar_version: "1.0"` | Permite evolución |
| **Metadatado** | Incluye framing + notas | Impide mal-interpretación |
| **Sin side-effects** | Solo lectura de BD | Safe para llamar múltiples veces |

---

## 3. VISTA STREAMLIT: radar_view()

### Ubicación

```python
# En app.py, alrededor de línea 2470

def radar_view():
    """
    Renderiza catálogo vivo como página Streamlit.

    Estructura:
    ├─ Encabezado + explicación
    ├─ Botón toggle: "Mostrar modelos internos" (debug)
    ├─ Resumen: providers, modelos, modos
    ├─ Listado por provider
    ├─ Listado por mode
    └─ Metadata de generación
    """
```

### Componentes Streamlit

#### 1. Header

```python
st.header("🎯 Radar: Catálogo Vivo")
st.markdown("""
**Snapshot del catálogo de PWR en este momento.**

Qué ves aquí:
- **Providers**: Quién provee los modelos (Gemini, Mock)
- **Modelos**: Qué LLMs están disponibles hoy
- **Modos**: Cómo PWR los organiza (Eco, Racing)
- **Capacidades**: Qué pueden hacer (vision, reasoning, etc)

Qué NO ves aquí (todavía):
- ❌ Histórico de uso
- ❌ Benchmarking
- ❌ Health monitor
- ❌ Scoring adaptativo

*Radar v1 es un snapshot honesto del catálogo vivo.*
""")
```

#### 2. Control Toggle

```python
col1, col2 = st.columns([0.7, 0.3])
with col2:
    show_internal = st.checkbox(
        "🔧 Mostrar internos",
        value=False,
        help="Modelos mock/test solo para debugging"
    )
```

#### 3. Build Snapshot

```python
radar = build_radar_snapshot(internal=show_internal)

if radar["status"] != "ok":
    st.error(f"Error: {radar.get('error', 'Unknown')}")
    return

radar_data = radar["radar"]
metadata = radar["metadata"]
```

#### 4. Summary Section

```python
st.subheader("📊 Resumen")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Providers", radar_data["summary"]["total_providers"])
with col2:
    st.metric("Modelos", radar_data["summary"]["total_models"])
with col3:
    st.metric("Modos", len(radar_data["summary"]["modes_list"]))
with col4:
    st.metric("Por defecto", radar_data["summary"]["default_mode"])
```

#### 5. Providers Section

```python
st.subheader("🔌 Providers")

for provider_name in sorted(radar_data["providers"].keys()):
    provider = radar_data["providers"][provider_name]

    with st.expander(f"**{provider_name.upper()}** ({len(provider['models'])} modelos)"):
        for model in provider["models"]:
            col1, col2, col3 = st.columns([0.4, 0.3, 0.3])

            with col1:
                # Nombre + status
                status_emoji = "🟢" if model["status"] == "active" else "🟡"
                internal_badge = " [INTERNAL]" if model["is_internal"] else ""
                st.write(f"{status_emoji} **{model['name']}{internal_badge}**")

            with col2:
                # Mode + cost
                st.caption(f"📌 {model['mode']} | 💰 ${model['estimated_cost_per_run']:.3f}")

            with col3:
                # Capabilities badges
                caps = model.get("capabilities", {})
                badges = []
                if caps.get("vision"):
                    badges.append("👁️ Vision")
                if caps.get("reasoning"):
                    badges.append("🧠 Reasoning")
                if caps.get("code_execution"):
                    badges.append("💻 Code")
                st.caption(" · ".join(badges) if badges else "—")

            # Full model details
            with st.expander("Detalles"):
                st.write(f"""
                - **Status**: {model['status']}
                - **Provider**: {model['provider']}
                - **Mode**: {model['mode']}
                - **Context Window**: {model['context_window']:,} tokens
                - **Estimated Cost**: ${model['estimated_cost_per_run']:.4f}
                - **Capabilities**: {model.get('capabilities', {})}
                """)
```

#### 6. Modes Section

```python
st.subheader("⚙️ Modos")

for mode_name in radar_data["summary"]["modes_list"]:
    mode = radar_data["modes"][mode_name]

    with st.expander(f"**{mode['label']}** ({mode_name})"):
        st.write(mode['description'])
        st.caption(f"Modelos: {', '.join(mode['models'])}")
```

#### 7. Metadata Footer

```python
st.divider()

col1, col2 = st.columns([0.7, 0.3])
with col1:
    st.caption(f"Generado: {metadata['generated_at']}")
    st.caption(f"Versión: {metadata['radar_version']} · Fuente: {metadata['catalog_source']}")

with col2:
    if show_internal:
        st.warning("⚠️ Modelos internos incluidos (debug)")

st.markdown(f"*{metadata['framing']}*")
st.markdown(f"*Nota: {metadata['note']}*")
```

---

## 4. ESTRUCTURA JSON BASE

### Snapshot JSON (desde build_radar_snapshot)

```json
{
  "status": "ok",
  "radar": {
    "providers": {
      "gemini": {
        "name": "gemini",
        "models": [
          {
            "id": "gemini-2.5-flash-lite",
            "name": "gemini-2.5-flash-lite",
            "provider": "gemini",
            "mode": "eco",
            "status": "active",
            "is_internal": false,
            "estimated_cost_per_run": 0.05,
            "context_window": 1000000,
            "capabilities": {
              "vision": false,
              "reasoning": false,
              "code_execution": true
            }
          },
          {
            "id": "gemini-2.5-pro",
            "name": "gemini-2.5-pro",
            "provider": "gemini",
            "mode": "racing",
            "status": "active",
            "is_internal": false,
            "estimated_cost_per_run": 0.30,
            "context_window": 2000000,
            "capabilities": {
              "vision": true,
              "reasoning": true,
              "code_execution": true
            }
          }
        ]
      }
    },
    "modes": {
      "eco": {
        "name": "eco",
        "label": "Económico",
        "description": "Rápido, barato, para tareas simples",
        "models": [
          "gemini-2.5-flash-lite"
        ]
      },
      "racing": {
        "name": "racing",
        "label": "Potencia máxima",
        "description": "Lento, caro, para tareas complejas",
        "models": [
          "gemini-2.5-pro"
        ]
      }
    },
    "summary": {
      "total_providers": 1,
      "total_models": 2,
      "providers_list": ["gemini"],
      "modes_list": ["eco", "racing"],
      "default_mode": "eco"
    }
  },
  "metadata": {
    "generated_at": "2026-04-17T18:32:49",
    "radar_version": "1.0",
    "catalog_source": "model_catalog BD",
    "framing": "live catalog snapshot – NOT observatorio histórico, NOT benchmarking, NOT health monitor, NOT adaptive scoring",
    "note": "Mode = temporal bridge to router_policy table (future)",
    "include_internal": false
  }
}
```

---

## 5. PREPARACIÓN PARA FUTURA API REAL

### Decisiones de Diseño para E3+ (API REST)

El snapshot está diseñado para ser reutilizable por una futura API:

#### Parámetros REST-Ready

```python
# Hoy: build_radar_snapshot(internal=False)
# Mañana: GET /api/radar?internal=false&version=1.0

# La función es agnóstica a cómo se llama
```

#### Estructura JSON agnóstica a transporte

- ✅ JSON serializable (no hay objetos custom)
- ✅ Campos tipados claramente
- ✅ Metadata versioned
- ✅ Status + error handling estándar

#### Error Handling ya diseñado

```json
{
  "status": "error",
  "error": "Catalog unavailable: database connection failed",
  "metadata": { "generated_at": "...", "radar_version": "1.0" }
}
```

#### Reutilización sin cambios

```python
# E1b: Streamlit
snapshot = build_radar_snapshot(internal=False)
render_snapshot_in_streamlit(snapshot)

# E2: Export JSON
snapshot = build_radar_snapshot(internal=False)
save_json_file("radar_export.json", snapshot)

# E3: Flask API
@app.route("/api/radar")
def api_radar():
    snapshot = build_radar_snapshot(internal=request.args.get("internal", False))
    return jsonify(snapshot)
    # Cero cambios en lógica, solo transporte
```

### Lo que NO hace la snapshot (para preservar simplicidad)

- ❌ Autenticación (preparado para agregar en E3)
- ❌ Rate limiting (preparado para agregar en E3)
- ❌ Paginación (no necesaria ahora, agregar después)
- ❌ Filtering query (keep it simple ahora)
- ❌ Caching HTTP headers (agregar en E3 si necesario)

---

## 6. FUERA DE SCOPE E1

| Cosa | Razón | Cuándo |
|------|-------|--------|
| API REST `/api/radar` | Streamlit puro, evitar complejidad | E3+ (si es necesario) |
| Autenticación | Catálogo es público y honesto | E3+ (si es necesario) |
| Histórico de cambios | No es observatorio | E3+ (Observatorio real) |
| Métricas de uso | Idem | E3+ |
| Benchmarking | Idem | E3+ |
| Export automático | Solo renderizar hoy | E2+ (si es necesario) |
| Caching avanzado | Keep it simple | E3+ |
| Alertas | Idem | E3+ |

---

## 7. ROUTING EN STREAMLIT (main())

### Estructura Actual

```python
def main():
    # Streamlit config, sidebar, etc.
    ...
    if st.session_state.get("active_project_id"):
        render_header()
        project_view()
    else:
        home_view()

if __name__ == "__main__":
    main()
```

### Modificación Mínima

```python
def main():
    # Streamlit config, sidebar, etc.
    ...

    # ==================== NEW: Radar View Switch ====================
    show_radar = st.sidebar.button("📡 Radar", use_container_width=True)

    if show_radar:
        st.session_state["view"] = "radar"
        # Force rerun
        st.rerun()

    # Routing
    view = st.session_state.get("view", "home")

    if view == "radar":
        radar_view()
    elif st.session_state.get("active_project_id"):
        render_header()
        project_view()
    else:
        home_view()

if __name__ == "__main__":
    main()
```

---

## 8. RESUMEN TÉCNICO E1

| Aspecto | Decisión |
|---------|----------|
| **Arquitectura** | Snapshot layer (reutilizable) + Vista Streamlit |
| **Snapshot function** | `build_radar_snapshot(internal=False) -> dict` |
| **Vista** | `radar_view()` con Streamlit UI |
| **JSON** | Limpio, versionado, agnóstico a transporte |
| **Routing** | Switch mínimo en main() |
| **Reutilización** | Preparada para E2 (export) + E3 (API) sin cambios |
| **Scope** | Solo snapshot + visualización, NADA más |

---

## ARCHIVOS EXACTOS A TOCAR (v2)

```
MODIFICADOS:
├─ router/model_catalog.py
│  └─ export_public_catalog() ya existe (E0)
│     [Sin cambios adicionales]
│
└─ app.py
   ├─ Agregar función build_radar_snapshot(internal=False) ~ línea 2450
   │  └─ Instancia ModelCatalog + export + metadata
   │
   ├─ Agregar función radar_view() ~ línea 2470
   │  └─ Renderiza con Streamlit components
   │
   └─ Modificar main() ~ línea 2500
      └─ Agregar routing: if view == "radar" → radar_view()

CREADOS:
└─ E1_SNAPSHOT_TEST.py
   └─ Tests de snapshot + validación de JSON
```

---

## STATUS TECH E1v2

```
Objetivo actual: Microplan actualizado con arquitectura sin Flask
Hecho:          Microplan completo (8 secciones + decisiones de diseño)
En progreso:    NINGUNO (esperando autorización)
Bloqueos:       NINGUNO
Riesgos:        NINGUNO (arquitectura simple y limpia)

Decisión que necesito de Albert:
  ✅ ¿Procedo a implementación con este plan?
  ❓ ¿Cambios a estructura o scope?
  ❓ ¿Agregar algo más a radar_view()?
```

