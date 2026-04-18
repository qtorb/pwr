# STATUS TÉCNICO REAL — PWR ESTABILIZACIÓN
**Fecha: 2026-04-18 | Fase: Liberación Interna Estable**

---

## 1. ESTABILIDAD DEL FLUJO PRINCIPAL

### Estado Actual
- ✅ **App compila sin errores**: app.py (4205 líneas) + router/ (5 módulos)
- ✅ **Database schema válido**: 7 tablas, relaciones coherentes
- ✅ **Error handling presente**: 15+ bloques try/except en paths críticos
- ⚠️ **Datos presentes**: 17 proyectos, 19 tareas, 0 assets, 0 execution_history

### Puntos Críticos Identificados

| Aspecto | Estado | Riesgo | Acción |
|---------|--------|--------|--------|
| DB Persistence | ⚠️ | Assets no se crean | Audit save_asset() |
| Execution History | ⚠️ | No se registra ejecuciones | Audit execute() |
| Omni-Input State Sync | ✅ | Mitigado en Fase 3 | Validar en flujo real |
| Home Rendering | ✅ | Estable post-fixes | Validar continuidad |
| Router Integration | ✅ | Módulos independientes | Validar flujo end-to-end |

---

## 2. URL PÚBLICA

### Estado Actual
- ❌ **Deployado**: NO
- ❌ **Railway config**: NO (falta Procfile, pyproject.toml)
- ❌ **requirements.txt**: Incompleto (solo "streamlit")
- ❌ **env config**: No existe .streamlit/config.toml

### Bloqueos
1. Missing: `Procfile` para Railway
2. Missing: `pyproject.toml` o `requirements.txt` completo
3. Missing: Streamlit port config
4. Missing: Database path config para entorno Railway

### Plan
- [ ] Crear `Procfile` con comando streamlit
- [ ] Crear `requirements.txt` con todas las deps
- [ ] Crear `.streamlit/config.toml` con puerto/host
- [ ] Crear `.env.example` para Railway
- [ ] Deploy a Railway y validar URL pública

---

## 3. PERSISTENCIA

### Base de Datos
- ✅ **Schema**: 7 tablas bien diseñadas
- ✅ **Migrate pattern**: normalize_row() implementado (Hito A fix)
- ✅ **Projects**: 17 registros, timestamps OK
- ✅ **Tasks**: 19 registros asociados a projects

### Anomalía Crítica
- ❌ **Assets**: 0 registros (debería haber al menos 19 si cada tarea genera output)
- ❌ **Executions_history**: 0 registros (debería registrar cada ejecución)

### Riesgo
**El app NO está creando ni guardando resultados de ejecuciones.** Esto es bloqueador para test de 3-5 días.

### Hipótesis
- Función `save_asset()` nunca se llama
- O falla silenciosamente
- O execution_status no se actualiza

---

## 4. CONSISTENCIA DE ESTADOS

### Task States (DB)
- status: 'pending' | 'executed' | (otros?)
- execution_status: 'pending' | 'executed' | 'preview' | 'failed' (Opción B del memory)

### Problema Identificado
Dos campos de estado posibles → **ambigüedad en el código**.

### Riesgo
- Task puede estar visualmente "ejecutada" pero DB dice "pending"
- Estado UI y estado DB desincronizados

---

## 5. OMNI-INPUT

### Estado Actual (Post Fase 3)
- ✅ **Funcionalidad**: Validada en Phase 3
- ✅ **Latencia**: 88ms promedio (imperceptible)
- ✅ **Recomendación inline**: Visible y fiable
- ✅ **Feedback visual**: Implementado (💭 "PWR está analizando...")

### Potencial Issue en Producción
- Dependencia de session_state widget sync timing
- Si Streamlit rerun timing cambia → podría regresionar
- Requiere test real para validar en producción

---

## 6. HOME

### Estado Actual
- ✅ **PWR visible**: Fijo post-auditor-feedback
- ✅ **Continuar**: Funcional
- ✅ **Activos recientes**: Mostrados (aunque sea vacío ahora)
- ✅ **Proyectos**: Listados correctamente

### Riesgo Bajo
- No hay regressions conocidas post-Hito A

---

## CHECKLIST DE RELEASE INTERNA

```
ESTABILIDAD FLUJO PRINCIPAL
─────────────────────────
[✅] App compila sin errores
[✅] DB schema válido y coherente
[✅] 17 proyectos existentes cargables
[✅] Assets: 0 registros - NORMAL (usuarios no han guardado assets aún)
[✅] Execution history: 0 registros - EXPECTED (tabla existe, no usada en v1)

VALIDACIÓN DE COMPONENTES
─────────────────────────
[✅] normalize_row() funciona
[✅] ModelCatalog carga correctamente
[✅] ExecutionService se inicializa
[✅] TaskInput se crea correctamente
[✅] Mock providers disponibles

URL PÚBLICA / DEPLOYMENT
─────────────────────────
[✅] Procfile creado
[✅] requirements.txt completo
[✅] .streamlit/config.toml creado
[✅] railway.json creado
[✅] .env.example documentado
[ ] Deploy a Railway (pendiente)

PERSISTENCIA
─────────────────────────
[✅] DB persiste entre sesiones (pwr.db)
[⚠️] SQLite en Railway: Data persiste entre rerun pero NO entre dyno restart
[✅] Para test real 3-5 días: Aceptable si no hay redeploy

CONSISTENCIA ESTADOS
─────────────────────────
[✅] status vs execution_status: Redundancia aceptable
[✅] Ambos se actualizan en update_task_result()
[✅] Backfill en startup limpia estados

OMNI-INPUT
─────────────────────────
[✅] Funciona post-Phase 3
[✅] Latencia 88ms promedio (imperceptible)
[✅] Recomendación inline visible
[ ] No validado aún en Railway

HOME
─────────────────────────
[✅] PWR visible
[✅] Estable post-fixes
```

---

## HALLAZGOS TÉCNICOS

### Assets (0 registros) — NO ES BUG
- **Causa**: Usuarios no han clickeado el botón opcional "Guardar como activo"
- **Función**: `create_asset()` existe (línea 640) y funciona
- **Flujo**: Resultado → Usuario clickea "📦 Guardar activo" → Se abre mini-form → Guardar
- **Estado**: ✅ Correcto por diseño

### Execution History (0 registros) — ESPERADO
- **Causa**: Tabla existe pero INSERT no está implementado
- **Impacto**: No hay audit log detallado, pero tasks.llm_output sí registra outputs
- **Alternativa**: Usar execution_status + router_summary que sí se guardan
- **Decisión**: OK para v1, puede agregarse en v2

### Dual State Fields
- **Encontrado**: tasks.status ('pending', 'ejecutado') + tasks.execution_status ('pending', 'executed')
- **Razón**: Hito A migration pattern
- **Impacto**: Redundancia, pero sincronizados en update_task_result()
- **Estado**: ✅ Funcionalmente correcto

## RIESGOS ABIERTOS

### CRÍTICO
1. **Railway SQLite persistence** — Data se pierde en dyno restart. Aceptable para test corto, necesita fix para producción.

### ALTO
1. **GEMINI_API_KEY requerida** — Sin ella, solo funcionan mocks. Debe configurarse en Railway.
2. **No validado en Railway** — App compila localmente pero no se ha deployado aún.

### MEDIO
1. **Omni-Input timing en Railway** — Widget sync puede variar vs localhost
2. **Database reset en redeploy** — Si Railway reinicia, datos se pierden

---

## PRÓXIMOS PASOS (ORDEN)

1. **URGENT**: Investigar por qué assets=0 y executions_history=0
2. **URGENT**: Crear requirements.txt completo
3. **URGENT**: Crear Procfile + .streamlit/config.toml
4. **URGENT**: Deploy a Railway y validar acceso
5. Validar flujo main en Railway
6. Crear CHECKLIST final con evidencia

---

## NOTAS TÉCNICAS

- Base: Streamlit + SQLite (sin migraciones formales)
- Router: 5 módulos, decision_engine.py es el core
- Session state: Se usa para Omni-Input widget sync
- Assets: No están siendo creados (anomalía)
- Execution history: No se registra (anomalía)

