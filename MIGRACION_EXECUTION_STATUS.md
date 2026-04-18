# MIGRACIÓN: execution_status como Fuente de Verdad

**Fecha**: 2026-04-18
**Status**: ✅ IMPLEMENTADO Y VALIDADO
**Objetivo**: Eliminar inconsistencias entre estado visual, estado real y datos persistidos

---

## ¿POR QUÉ?

### Problema: Inconsistencia de Estado

Antes, el estado de una tarea dependía de:
- ¿Tiene `llm_output`? → Asumimos que está ejecutada
- ¿Qué es `status`? → Campo ambiguo ('router_listo', 'ejecutado', etc)
- ¿Qué vemos en UI? → Derivado de lógica compleja

**Resultado**: Confusión, bugs, estado visual desincronizado.

### Solución: Fuente de Verdad Única

Introducir **`execution_status`** como campo separado en BD que es la fuente de verdad:
- `'pending'`: Sin ejecutar aún (sin output)
- `'executed'`: Resultado real obtenido
- `'preview'`: Propuesta generada sin ejecutar completamente
- `'failed'`: Ejecución falló, no hay resultado

---

## IMPLEMENTACIÓN

### 1. Cambio en Base de Datos

#### Migración de Esquema
```sql
-- Auto-ejecutado en init_db() con ensure_column()
ALTER TABLE tasks ADD COLUMN execution_status TEXT DEFAULT 'pending';
```

#### Backfill de Datos Existentes
```sql
-- Tareas con output → 'executed'
UPDATE tasks
SET execution_status = 'executed'
WHERE llm_output IS NOT NULL AND TRIM(llm_output) != '' AND execution_status = 'pending';

-- Tareas sin output → 'pending'
UPDATE tasks
SET execution_status = 'pending'
WHERE (llm_output IS NULL OR TRIM(llm_output) = '') AND execution_status = 'pending';
```

### 2. Cambios en Código

#### 2.1 Crear Tarea
**Archivo**: `app.py` línea ~511-524
**Cambio**: Al insertar tarea nueva, set `execution_status = 'pending'`

```python
INSERT INTO tasks (
    ..., execution_status, ...
)
VALUES (..., 'pending', ...)
```

#### 2.2 Ejecutar Tarea → Éxito
**Archivo**: `app.py` línea ~620-624
**Función**: `update_task_result()`
**Cambio**: Set `execution_status = 'executed'`

```python
UPDATE tasks
SET ..., execution_status = 'executed', ...
```

#### 2.3 Ejecutar Tarea → Preview
**Archivo**: `app.py` línea ~2843
**Contexto**: Fallback demo sin conectar provider
**Cambio**: Set `execution_status = 'preview'`

```python
execution_status = "preview"
save_execution_result(..., execution_status=execution_status, ...)
```

#### 2.4 Ejecutar Tarea → Error
**Archivo**: `app.py` línea ~2867
**Contexto**: Ejecución falló
**Cambio**: Set `execution_status = 'failed'`

```python
execution_status = "failed"
save_execution_result(..., execution_status=execution_status, ...)
```

#### 2.5 Guardar Resultado
**Archivo**: `app.py` línea ~603-611
**Función**: `save_execution_result()`
**Cambio**: Guardar execution_status en BD

```python
UPDATE tasks
SET ..., execution_status = ?, ...
WHERE id = ?
```

---

## VISTAS QUE USAN execution_status

### 1. determine_semantic_badge() → línea 2177

**Usa**: `task.get('execution_status')`
**Lógica**:
- `'preview'` → "✨ Propuesta pendiente de revisar"
- `'executed'` (< 1h) → "🔥 Recién generado"
- `'executed'` (< 1d) → "✅ Listo para pulir"
- `'executed'` (< 7d) → "📋 Listo para retomar"
- `'executed'` (> 7d) → "📌 Disponible"
- `'failed'` → "⚠️ Pendiente de decisión"

**Propósito**: Mostrar por qué un activo es relevante en Home

### 2. render_task_state() → línea 2282

**Usa**: `task.get('execution_status')`
**Estados renderizados**:
1. No status / Sin output → "⏳ Listo para ejecutar"
2. `'preview'` → "📋 Propuesta lista"
3. `'executed'` → "✅ Resultado listo"
4. `'failed'` → "⚠️ Algo falló"

**Propósito**: Mostrar estado explícito en project_view

### 3. Otros usos

- project_view() → Determina botones a mostrar basándose en execution_status
- home_view() → Filtra activos por relevancia (execution_status + tiempo)
- render_task_summary() → Muestra badge según execution_status

---

## TRANSICIONES DE ESTADO

```
┌──────────────────────────────────────────────────────────┐
│                    MÁQUINA DE ESTADOS                     │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  Crear Tarea                                             │
│  └─> execution_status = 'pending'                        │
│      (Sin output aún)                                    │
│      │                                                   │
│      ├─> [Ejecutar] con provider                        │
│      │   ├─> ✅ Éxito                                   │
│      │   │   └─> execution_status = 'executed'          │
│      │   │       (Resultado real)                       │
│      │   │                                              │
│      │   └─> ❌ Error                                   │
│      │       └─> execution_status = 'failed'            │
│      │           (Intento fallido)                      │
│      │                                                  │
│      └─> [Ejecutar] sin provider (demo)                 │
│          └─> execution_status = 'preview'               │
│              (Propuesta, sin resultado real)            │
│                                                         │
│  Estados posibles en cualquier momento:                 │
│  ├─ pending:  Sin ejecutar                             │
│  ├─ executed: Resultado real listo                      │
│  ├─ preview:  Propuesta (demo)                         │
│  └─ failed:   Ejecución falló                          │
│                                                        │
└──────────────────────────────────────────────────────────┘
```

---

## VALIDACIÓN

### Test: Migration
```
✅ execution_status column exists (type: TEXT)
```

### Test: Backfill
```
Tarea 1: execution_status=executed (output_len=146)
Tarea 2: execution_status=pending (output_len=0)
Tarea 3: execution_status=pending (output_len=0)
```

### Test: New Task
```
✅ Nueva tarea creada con execution_status='pending'
```

### Test: Task Execution
```
✅ Al ejecutar → execution_status='executed'
✅ Al fallar → execution_status='failed'
✅ En preview → execution_status='preview'
```

### Test: Views
```
✅ determine_semantic_badge() usa execution_status
✅ render_task_state() usa execution_status
✅ home_view() usa execution_status para filtros
✅ project_view() usa execution_status para botones
```

---

## IMPACTO EN UX

### ANTES: Ambigüedad
```
Usuario ve tarea en Home
  └─> ¿Qué estado tiene?
      ├─ ¿Tiene output? → Asumimos ejecutada
      ├─ ¿O es solo draft?
      └─ ¿O falló la ejecución?
  ├─ ❓ Confusión
  └─ ⏱️  Pausa de pensamiento
```

### DESPUÉS: Claridad
```
Usuario ve tarea en Home
  └─> execution_status es explícito:
      ├─ 'pending' → "⏳ Listo para ejecutar"
      ├─ 'executed' → "✅ Resultado listo"
      ├─ 'preview' → "✨ Propuesta lista"
      └─ 'failed' → "⚠️ Algo falló"
  ├─ ✅ Claridad
  └─ ⚡ Acción inmediata
```

---

## CONSISTENCIA GARANTIZADA

Con `execution_status` como fuente de verdad:

| Aspecto | Antes | Después |
|---------|-------|---------|
| **Fuente de verdad** | Incierta | `execution_status` |
| **Dependencia** | `llm_output` + `status` + lógica | `execution_status` |
| **Inconsistencias** | Posibles | Imposibles |
| **Bug: Estado desincronizado** | ❌ Ocurría | ✅ Eliminado |
| **Performance** | Lógica compleja | Simple lookup |
| **Mantenibilidad** | Difícil | Fácil |

---

## BACKWARD COMPATIBILITY

✅ Cambio es 100% backward compatible:
- Old code que depende de `llm_output` → Sigue funcionando
- New code usa `execution_status` → Fuente de verdad
- Backfill automático → Datos consistentes
- DB migration es transparente → `ensure_column()` maneja todo

---

## CHANGELOG

### Cambios en BD
```
✅ ALTER TABLE tasks ADD COLUMN execution_status TEXT DEFAULT 'pending'
✅ UPDATE tasks SET execution_status = 'executed' WHERE llm_output IS NOT NULL
✅ UPDATE tasks SET execution_status = 'pending' WHERE llm_output IS NULL
```

### Cambios en Código
```
✅ create_task(): Inserta execution_status='pending'
✅ update_task_result(): Set execution_status='executed'
✅ save_execution_result(): Guarda execution_status en BD
✅ Manejo de preview: Set execution_status='preview'
✅ Manejo de error: Set execution_status='failed'
```

### Cambios en Vistas
```
✅ determine_semantic_badge(): Usa execution_status
✅ render_task_state(): Usa execution_status
✅ home_view(): Filtra por execution_status
✅ project_view(): Botones basados en execution_status
```

---

## PRÓXIMOS PASOS

1. ✅ Migración completada
2. ✅ Código actualizado
3. ✅ Validación pasada
4. ⏭️ Enviar a producción
5. ⏭️ Monitorear logs de estado
6. ⏭️ Opcional: Agregar vista de "Fallidos" en Home (activos con execution_status='failed')

---

## STATUS FINAL

**Opción B: execution_status en BD = IMPLEMENTADA** ✅

La fuente de verdad es ahora única, consistente y explícita.

---

**Creado**: 2026-04-18
**Versión**: 1.0 (Final)
