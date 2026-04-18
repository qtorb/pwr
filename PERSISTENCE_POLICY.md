# PERSISTENCE POLICY: Qué Guardamos y Por Qué

**Fecha**: 2026-04-17
**Bloque**: F (Onboarding + Persistencia Útil)
**Propósito**: Claridad sobre qué datos persisten en PWR y por qué.

---

## FILOSOFÍA

> **Guardamos lo que el usuario ve y reutiliza.**
>
> Histórico, análisis y métricas avanzadas vienen después (E2+).

---

## QUÉ GUARDAMOS (OBLIGATORIO)

Estos datos persisten porque el usuario los ve y necesita reutilizarlos.

### 1. Proyectos (`projects` table)

```
Campos: name, slug, description, objective, base_context, base_instructions, tags

Por qué:
  - Organizan el trabajo del usuario
  - Son reutilizables: puedo volver a un proyecto en 3 meses
  - Contexto y instrucciones se reutilizan para nuevas tareas
```

### 2. Tareas (`tasks` table)

```
Campos: title, description, type, context, status

Por qué:
  - Historial de qué hizo el usuario
  - Trazabilidad: "hace 2 semanas pregunté X"
  - Reutilizable: puedo duplicar una tarea
```

### 3. Resultados (`llm_output`, `useful_extract` en `tasks`)

```
Campos: llm_output (completo), useful_extract (resumen 700 chars)

Por qué:
  - ES EL DELIVERABLE. Sin esto, PWR no sirve.
  - Usuario edita, reutiliza, comparte resultado
  - Necesario para convertir en "asset" (documento guardado)
```

### 4. Decisión del Router (`router_summary` en `tasks`)

```
Campos: "Modo: eco, Modelo: gemini-2.5-flash-lite, Latencia: 1200ms, Costo: $0.05"

Por qué:
  - Explicación de qué PWR eligió y por qué
  - Transparencia: usuario entiende la decisión
  - Trazabilidad: por qué se usó ese modelo
```

### 5. Deliverables procesados (`assets` table)

```
Campos: title, summary, content (procesado/estructurado)

Por qué:
  - Resultado final reutilizable (documento, email, código, etc)
  - Puede guardarse/exportarse/compartirse
  - Historial de deliverables creados
```

### 6. Catálogo vivo (`model_catalog` table)

```
Campos: provider, model_name, mode, estimated_cost_per_run, capabilities_json, status

Por qué:
  - Configuración del sistema
  - DecisionEngine la consulta para elegir modelo
  - PWR actualiza esto si hay nuevos providers
```

---

## QUÉ GUARDAMOS PERO NO USAMOS AÚN (ESPERAR E2+)

Estos campos existen pero su uso está en pausa.

### router_metrics_json (en `tasks`)

```
Contenido: {"mode": "eco", "model": "...", "latency_ms": 1200, "estimated_cost": 0.05, ...}

Status: Guardado, no usado aún

Por qué después (E2+):
  - Dashboard de uso por usuario
  - Estadísticas: "usé eco 80% del tiempo"
  - Análisis de costos
  - Observatorio de decisiones
```

### executions_history (tabla)

```
Contenido: Fila por cada ejecución (task_id, mode, model, provider, latency_ms, cost)

Status: Tabla creada, no consultada aún

Por qué después (E2+):
  - Tabla de histórico de ejecuciones
  - Reportes: "últimas 10 tareas resueltas"
  - Auditoría de uso
```

---

## QUÉ NO GUARDAMOS (DELIBERADAMENTE)

Estos datos NO persisten porque aún no agregan valor o tienen riesgos.

### Logging técnico granular

```
❌ NO guardamos: scores internos, umbrales de DecisionEngine, traces de decisión

Por qué no:
  - DecisionEngine es "caja negra" intencional
  - Usuario no necesita ver esto
  - Agrega complejidad sin beneficio
```

### Métricas agregadas

```
❌ NO guardamos: "tareas totales resueltas", "costo total", "modelo favorito"

Por qué no:
  - Sin dashboard, nadie las ve
  - Se calculan sobre la marcha si se necesitan
  - Esperar E2 para definir qué métricas importan
```

### Preferencias de usuario

```
❌ NO guardamos: tema oscuro, idioma, notificaciones, layout preference

Por qué no:
  - Aún no es multiusuario
  - Una persona usa PWR
  - Agregará complejidad sin ROI ahora
```

### API keys o secretos

```
❌ NO guardamos: API keys de providers, tokens, credentials

Por qué no:
  - Peligroso guardar en BD
  - Mejor: env vars o admin panel (E3+)
  - Cumplimiento: no persistir secretos en BD
```

### Logs de auditoría completos

```
❌ NO guardamos: "Usuario X hizo Y a las 14:32", "Cambio en proyecto Z"

Por qué no:
  - Overkill para prototipo
  - Cumplimiento/compliance: E3+
  - Aún sin requerimientos de auditoría
```

---

## IMPACTO: SI NO GUARDÁRAMOS ESTO

| Entidad | Si NO guardamos | Impacto |
|---------|-----------------|--------|
| projects | Usuario pierde historial completo | ❌ Crítico |
| tasks | Usuario no ve qué hizo | ❌ Crítico |
| llm_output | Desaparece el deliverable | ❌ Crítico |
| router_summary | Usuario no entiende decisiones | ⚠️ Alto |
| assets | No hay deliverables procesados | ⚠️ Alto |
| model_catalog | PWR no sabe qué modelos existen | ❌ Crítico |
| router_metrics_json | Sin observatorio (acepto esperar) | ✅ OK (E2) |
| executions_history | Sin historial detallado (acepto esperar) | ✅ OK (E2) |

---

## VISIBILIDAD AL USUARIO

### En Home / Proyectos

```
Usuario ve:
✅ "Mi proyecto X" (proyecto guardado)
✅ "Tarea: Resume documento" (tarea guardada)
✅ "Resultado: [preview del output]" (deliverable guardado)
✅ "PWR eligió: eco mode, gemini-2.5-flash-lite" (decisión guardada)
```

### En Radar

```
Usuario ve:
✅ "Gemini-2.5-flash-lite" (modelo guardado)
✅ "Capacidades: vision, reasoning" (configuración guardada)
✅ "Costo estimado: $0.05" (pricing guardado)
❌ "No hay histórico de cuándo se usó este modelo" (esperar E2)
```

### En Assets

```
Usuario ve:
✅ "Email profesional (draft)" (asset guardado, procesado)
✅ "Resumen ejecutivo (documento)" (deliverable reutilizable)
✅ "Ideas para LinkedIn (lista)" (contenido guardado)
```

### En Analytics / Observatorio (NO VISIBLE AÚN)

```
Usuario NO ve aún:
❌ "Tareas resueltas: 42"
❌ "Modo favorito: eco (72% del tiempo)"
❌ "Costo total: $15.43"

Esperar: E2 (cuando tenga sentido mostrar esto)
```

---

## DECISIONES IMPORTANTES

### 1. Qué hacemos si se cae la BD

```
¿Qué persiste?
✅ projects, tasks, outputs, router_summary, assets, model_catalog

Usuario esperaría:
"Recuperé mis proyectos. Los resultados están ahí. PWR funcionó bien."
```

### 2. Si un usuario pide "borrar mi historial"

```
Borramos:
✅ Sus proyectos y tareas (si quiere limpiar)
⚠️ No borramos model_catalog (es compartido, configuración del sistema)

No es asunto de Opción 1, pero es bueno saber el principio.
```

### 3. Si queremos exportar "mi historial de PWR"

```
Exportamos:
✅ Todos los proyectos
✅ Todas las tareas
✅ Todos los outputs y assets
✅ router_summary de cada tarea (decisiones)
✅ NOT router_metrics_json (para E2+)
✅ NOT executions_history detallado (para E2+)
```

---

## MENSAJE AL USUARIO

**En Home:**
> "PWR guarda tus proyectos, tareas y resultados.
>  Aquí siempre verás tu historial de trabajo.
>  Estadísticas y análisis vienen después."

**En Radar:**
> "Este es el catálogo de modelos que PWR consulta.
>  NO ves aquí cuándo se usó cada uno. Solo la configuración."

**En Settings (futuro, E3+):**
> "Exporta tu historial completo: proyectos, tareas, resultados.
>  Tus datos son tuyos."

---

## TIMELINE

```
AHORA (F):
├─ Confirmar persistencia mínima útil (este documento)
└─ Guardar: projects, tasks, outputs, router_summary, assets, model_catalog

DESPUÉS (E2):
├─ Mostrar router_metrics_json en observatorio
├─ Usar executions_history para reportes
└─ Agregar "Estadísticas" view

FUTURO (E3+):
├─ Export completo
├─ Audit trail
└─ Compliance
```

---

## SUMMARY

**Guardamos**: Lo que usuario ve y reutiliza (proyectos, tareas, resultados, decisiones).

**Preparamos**: Lo que usaremos en E2+ (métricas, histórico granular).

**No guardamos**: Lo que aún no importa (logging, preferences, secretos).

**Promesa**: "Tus trabajo está aquí. Futuro traerá insight."

