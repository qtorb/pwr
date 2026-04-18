# E1 MICROPLAN: `/radar` v1 - Catálogo Vivo Mínimo

**Fecha**: 2026-04-17
**Bloque**: E1 (Endpoint expuesto del catálogo vivo)
**Filosofía**: "Qué usa hoy PWR y cómo está organizado ese catálogo" — honesto, útil, no pretencioso.

---

## 1. ARCHIVOS A TOCAR

### Archivos Modificados

| Archivo | Cambio | Línea Aprox | Justificación |
|---------|--------|-------------|---------------|
| **app.py** | Agregar ruta Flask para `/api/radar` | ~2500+ | Nuevo endpoint productivo |
| **router/model_catalog.py** | Agregar método `export_public_catalog()` | ~200+ | Serializar catálogo visible |

### Archivos Creados

| Archivo | Propósito | Tipo |
|---------|-----------|------|
| **E1_VALIDATION.md** | Checklist de validación E1 | Documentación |

### Archivos NO tocados

- `router/decision_engine.py` — Sin cambios, DecisionEngine intacto
- `router/execution_service.py` — Sin cambios, providers intactos
- `router/domain.py` — Sin cambios, contratos intactos
- `test_e0_validation.py` — Conservado como reference

---

## 2. FORMA EXACTA DEL ENDPOINT

### Definición

```
GET /api/radar

Parámetros opcionales:
  - ?internal=false (default) → Oculta models con is_internal=1
  - ?internal=true (requiere validación futura) → Muestra todo (bloqueado por ahora)

Respuesta:
  - Content-Type: application/json
  - Status: 200 OK
  - Body: RadarResponse JSON (ver sección 3)

Errores:
  - 500: BD no disponible o query falla
    Respuesta: { "error": "Catalog unavailable", "status": "error" }
```

### Ubicación en app.py

```python
# Alrededor de línea 2500+ (después de vistas existentes, antes de @app.run)

@app.route("/api/radar", methods=["GET"])
def radar_endpoint():
    """
    Catálogo vivo de PWR: qué modelos y providers están disponibles hoy.

    Parámetros:
      - internal: bool (default=false) - Incluir modelos internos (mock, test)

    Respuesta:
      { "status": "ok|error", "catalog": {...}, "metadata": {...} }
    """
    try:
        include_internal = request.args.get("internal", "false").lower() == "true"

        # Obtener catálogo vivo desde BD
        with get_conn() as conn:
            catalog = ModelCatalog(conn)
            response = catalog.export_public_catalog(include_internal=include_internal)

        return jsonify({
            "status": "ok",
            "catalog": response,
            "metadata": {
                "generated_at": now_iso(),
                "version": "1.0",
                "source": "model_catalog BD"
            }
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "metadata": {
                "generated_at": now_iso(),
            }
        }), 500
```

---

## 3. ESTRUCTURA JSON DE RESPUESTA

### Respuesta 200 OK (Normal)

```json
{
  "status": "ok",
  "catalog": {
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
      },
      "mock": {
        "name": "mock",
        "models": [
          {
            "id": "mock-eco",
            "name": "mock-eco",
            "provider": "mock",
            "mode": "eco",
            "status": "active",
            "is_internal": true,
            "estimated_cost_per_run": 0.0,
            "context_window": 100000,
            "capabilities": {
              "vision": false,
              "reasoning": false,
              "code_execution": false
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
          "gemini-2.5-flash-lite",
          "mock-eco"
        ]
      },
      "racing": {
        "name": "racing",
        "label": "Potencia máxima",
        "description": "Lento, caro, para tareas complejas",
        "models": [
          "gemini-2.5-pro",
          "mock-racing"
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
    "generated_at": "2026-04-17T18:32:49.126016",
    "version": "1.0",
    "source": "model_catalog BD"
  }
}
```

### Respuesta 200 OK (Con ?internal=true)

```json
{
  "status": "ok",
  "catalog": {
    "providers": {
      "gemini": { ... },
      "mock": {
        "models": [
          { "id": "mock-eco", "is_internal": true, ... },
          { "id": "mock-racing", "is_internal": true, ... }
        ]
      }
    },
    ...
  },
  "metadata": {
    "generated_at": "2026-04-17T18:32:49.126016",
    "version": "1.0",
    "source": "model_catalog BD",
    "include_internal": true,
    "warning": "Internal models shown - for debugging only"
  }
}
```

### Respuesta 500 Error

```json
{
  "status": "error",
  "error": "Catalog unavailable: database connection failed",
  "metadata": {
    "generated_at": "2026-04-17T18:32:49.126016"
  }
}
```

---

## 4. CAMPOS INCLUIDOS Y EXCLUIDOS

### INCLUIDOS (Públicos, seguros)

| Campo | Razón | Ejemplo |
|-------|-------|---------|
| `provider` | Identifica source de LLM | "gemini", "mock" |
| `model_name` | Identificador único | "gemini-2.5-flash-lite" |
| `mode` | Categoría de ejecución | "eco", "racing" |
| `status` | Disponibilidad actual | "active", "deprecated" |
| `is_internal` | Marca modelos de test | true/false |
| `estimated_cost_per_run` | Coste visible al usuario | 0.05, 0.30 |
| `context_window` | Capacidad técnica | 1000000 |
| `capabilities_json` (parseado) | Qué puede hacer | {"vision": true, ...} |

### EXCLUIDOS (Internos, sensibles)

| Campo | Razón | Futuro |
|-------|-------|--------|
| `pricing_input_per_mtok` | Datos brutos, incompletos | Usar `estimated_cost_per_run` |
| `pricing_output_per_mtok` | Ídem anterior | Ídem |
| `deprecated_at` | Información interna | Mostrar en admin panel (E2+) |
| `id` (BD PK) | Innecesario externamente | Usar `model_name` como ID |
| `error_code` | No es catálogo, es métrica | Guardado en `executions_history` |
| `latency_ms` (histórico) | No es catálogo | Queryable vía `/api/executions` (E2+) |
| `complexity_score` | Decisión interna | No es configuración del catálogo |

### CONDICIONAL

| Campo | Incluido | Justificación |
|-------|----------|---------------|
| `mode` | SÍ, por ahora | BRIDGE TEMPORAL hasta router_policy table |
| `capabilities` | SÍ | Viene de BD, es honesto |
| `last_used` | NO en E1 | Requiere auditoría de executions_history (E2) |

---

## 5. FILTRADO DE DATOS INTERNOS (is_internal)

### Lógica de Filtrado

```python
# En ModelCatalog.export_public_catalog(include_internal=False)

def export_public_catalog(self, include_internal: bool = False):
    """
    Exporta catálogo vivo como JSON para /radar endpoint.

    Args:
        include_internal: Si False (default), filtra is_internal=1
    """
    catalog_data = {
        "providers": {},
        "modes": {},
        "summary": {}
    }

    for model_name, row in self._catalog_rows.items():
        # FILTRO: Saltar modelos internos si no autorizado
        if row.get("is_internal") == 1 and not include_internal:
            continue

        provider = row["provider"]
        if provider not in catalog_data["providers"]:
            catalog_data["providers"][provider] = {
                "name": provider,
                "models": []
            }

        # Serializar solo campos públicos
        public_model = {
            "id": model_name,
            "name": model_name,
            "provider": provider,
            "mode": row.get("mode"),
            "status": row.get("status", "active"),
            "is_internal": row.get("is_internal", 0),
            "estimated_cost_per_run": row.get("estimated_cost_per_run"),
            "context_window": row.get("context_window"),
            "capabilities": self._parse_capabilities(row.get("capabilities_json", "{}"))
        }

        catalog_data["providers"][provider]["models"].append(public_model)

    return catalog_data
```

### Casos de Filtrado

| Caso | Resultado |
|------|-----------|
| `is_internal=0` (real) + `?internal=false` | ✅ Incluido en respuesta |
| `is_internal=1` (mock) + `?internal=false` | ❌ Excluido de respuesta |
| `is_internal=1` (mock) + `?internal=true` | ✅ Incluido + warning en metadata |
| `status="deprecated"` | ✅ Incluido siempre (marcar `status`) |

---

## 6. RIESGOS DE EXPONER DATOS CONFUSOS O INCOMPLETOS

### Riesgo 1: `estimated_cost_per_run` sin contexto

**Problema**: Usuario ve "$0.05" sin saber si es por 100 tokens o 1000 tokens.

**Mitigación**:
```json
"estimated_cost_per_run": 0.05,
"_cost_note": "Valor estimado para tarea típica, no garantizado"
```
(NO agregamos nota, pero UI puede explicar)

**Honestidad**: ✅ Campo claramente etiquetado como "estimado", no "guaranteed"

---

### Riesgo 2: `capabilities` parseado de JSON incompleto

**Problema**: Si `capabilities_json` en BD es `"{}"`, qué mostramos?

**Mitigación**:
```python
def _parse_capabilities(self, json_str):
    try:
        caps = json.loads(json_str or "{}")
        # Garantizar campos mínimos
        return {
            "vision": caps.get("vision", False),
            "reasoning": caps.get("reasoning", False),
            "code_execution": caps.get("code_execution", False),
            # Agregar otros si existen
            **{k: v for k, v in caps.items() if k not in ["vision", "reasoning", "code_execution"]}
        }
    except:
        return {}  # Fallback honesto
```

**Honestidad**: ✅ Campos faltantes = `false` (no asumir), fallback a `{}`

---

### Riesgo 3: Mostrar `mode` como si fuera inmutable

**Problema**: Usuario ve `"mode": "eco"` y asume que eco SIEMPRE usa gemini-2.5-flash-lite. Pero DecisionEngine podría cambiar eso en futuro.

**Mitigación**:
```json
"metadata": {
  "version": "1.0",
  "source": "model_catalog BD",
  "note": "Mode is temporal bridge to router_policy; configuration may change per execution"
}
```

**Honestidad**: ✅ Docstring en ModelCatalog + metadata warning si es necesario

---

### Riesgo 4: mock modelos con `is_internal=true` confundiendo a usuarios

**Problema**: Usuario ve "mock-eco" y piensa "¿por qué hay un fake model en mi catálogo?"

**Mitigación**:
1. Default `?internal=false` → mock modelos NO visibles
2. Si alguien hace `?internal=true`, metadata tiene `"warning": "Internal models..."`
3. Documentar en README que `/api/radar?internal=true` es solo para debugging

**Honestidad**: ✅ Filtro por defecto + warning explícito

---

### Riesgo 5: `context_window` desactualizado en BD

**Problema**: Alguien cambia en BD a `999999` pero DecisionEngine usa otra info.

**Mitigación**:
- `context_window` es **configuración estática** del modelo, no métrica dinámica
- DecisionEngine usa DecisionEngine logic (en código), no `context_window` de BD
- `/radar` muestra lo que está en BD (honesto)
- Si desincronización es problema, es **señal de que Bloque D tiene bug**

**Honestidad**: ✅ /radar muestra estado real de BD, responsabilidad es mantener BD consistente

---

## 7. VALIDACIÓN: E1 es honesto y consistente

### Test 1: Catálogo no vacío

```python
GET /api/radar
Verificar:
  - status == "ok"
  - catalog.providers no vacío
  - catalog.providers["gemini"] contiene al menos gemini-2.5-flash-lite
  - Todos los modelos tienen provider, model_name, status
```

### Test 2: Filtrado is_internal

```python
GET /api/radar (default, internal=false)
Verificar:
  - No hay modelos con is_internal=1
  - Total_models >= 2 (gemini-2.5-flash-lite, gemini-2.5-pro)

GET /api/radar?internal=true
Verificar:
  - Hay modelos con is_internal=1 (mock-eco, mock-racing)
  - Total_models >= 4
  - metadata.warning presente
```

### Test 3: Estructura JSON válida

```python
GET /api/radar
Verificar:
  - JSON parseable
  - Campos requeridos presentes: provider, model_name, mode, status, is_internal, estimated_cost_per_run, context_window, capabilities
  - Tipos correctos: bool para is_internal, float para cost, int para context_window
  - capabilities es dict valid o {} (nunca null)
```

### Test 4: Consistencia con BD

```python
Query model_catalog table directly
Query /api/radar

Comparar:
  - Número de modelos activos (status='active') == cantidad en /radar (sin internal)
  - Nombres de modelos coinciden
  - capabilities_json parseado correctamente
  - estimated_cost_per_run coincide
```

### Test 5: Respuesta a errores

```python
Simular: BD unavailable / corrupted

Verificar:
  - Status 500
  - error field presente
  - Mensaje legible (no stack trace interno)
```

### Test 6: Responsabilidad honesta

```python
Verificar que /radar:
  ✅ No inventa modelos que no existen
  ✅ No oculta modelos activos sin razón
  ✅ No marca cosas como active si deprecated
  ✅ No reclama features que no están en capabilities
  ✅ No asegura disponibilidad (just reports status)
```

---

## RIESGOS IDENTIFICADOS Y MITIGATION

| Riesgo | Severidad | Mitigación | Status |
|--------|-----------|-----------|--------|
| Datos desincronizados entre BD y código | MEDIA | Validación en init_db() + test E1 | Pre-implement |
| Usuario malinterpreta estimated_cost_per_run | BAJA | Documentar en metadata | Pre-implement |
| mock modelos confunden a usuario | BAJA | Filter default + warning | Pre-implement |
| /radar se confunde con "observatorio real" | MEDIA | Metadata.note explícito | Pre-implement |
| is_internal=true expone info sensible | BAJA | No requiere auth, pero está marcado | Pre-implement |
| capabilities JSON incompleto | BAJA | Fallback a {} + defaults | Pre-implement |

---

## RESUMEN: RESPONSABILIDADES

### `/radar` ES (Catálogo Vivo)

✅ Configuración estática de qué modelos existen hoy
✅ Qué capacidades tienen
✅ Qué modo usa cada uno (BRIDGE TEMPORAL)
✅ Si están deprecated o active
✅ Coste estimado por run

### `/radar` NO ES (y nunca lo será en E1)

❌ Observatorio de uso histórico
❌ Predicción de latencias
❌ Scoring adaptativo
❌ Agregaciones de ejecuciones
❌ Autenticación / usuarios
❌ Datos sensibles de proyectos

---

## ARCHIVOS A CREAR/MODIFICAR (PRECISO)

```
MODIFICADOS:
├─ app.py
│  └─ Agregar @app.route("/api/radar") ~ línea 2500+
│     Instanciar ModelCatalog(conn)
│     Llamar catalog.export_public_catalog(include_internal)
│     Retornar JSON con status, catalog, metadata
│
└─ router/model_catalog.py
   └─ Agregar método export_public_catalog(include_internal=False)
      Filtrar is_internal
      Serializar solo campos públicos
      Retornar dict con providers, modes, summary
```

---

## STATUS TECH E1

**Objetivo actual**: Plan disciplinado de E1, listo para implementación
**Hecho**: Microplan completo con 7 secciones
**En progreso**: NINGUNO (esperando autorización)
**Bloqueos**: NINGUNO
**Riesgos identificados**: 6 (todos mitigados)
**Decisión que necesito de Albert**:
- ¿Procedo a implementación de E1 con este microplan?
- ¿Cambios al scope o estructura JSON?
- ¿Agregar validación de Test 6 como requerimiento?
