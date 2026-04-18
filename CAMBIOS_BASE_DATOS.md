# CAMBIOS EN BASE DE DATOS - Referencia Técnica

**Fecha**: 2026-04-18

---

## Schema Antes

```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    task_type TEXT DEFAULT 'Pensar',
    context TEXT DEFAULT '',
    status TEXT DEFAULT 'borrador',
    suggested_model TEXT DEFAULT '',
    router_summary TEXT DEFAULT '',
    llm_output TEXT DEFAULT '',
    useful_extract TEXT DEFAULT '',
    uploads_json TEXT DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(id)
)
```

**Notar**: NO hay execution_status

---

## Schema Después

```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    task_type TEXT DEFAULT 'Pensar',
    context TEXT DEFAULT '',
    status TEXT DEFAULT 'borrador',
    suggested_model TEXT DEFAULT '',
    router_summary TEXT DEFAULT '',
    llm_output TEXT DEFAULT '',
    useful_extract TEXT DEFAULT '',
    uploads_json TEXT DEFAULT '[]',
    execution_status TEXT DEFAULT 'pending',  ← NUEVO
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(id)
)
```

**Cambio**: Se agregó `execution_status TEXT DEFAULT 'pending'`

---

## Migración SQL

### Paso 1: Agregar Columna

```sql
ALTER TABLE tasks ADD COLUMN execution_status TEXT DEFAULT 'pending';
```

**Automático en**: `init_db()` → `ensure_column()` (línea 51-54)

### Paso 2: Backfill - Tareas Ejecutadas

```sql
UPDATE tasks
SET execution_status = 'executed'
WHERE llm_output IS NOT NULL AND TRIM(llm_output) != '' AND execution_status = 'pending';
```

**Lógica**: Si tiene output no vacío → fue ejecutada

**Ejemplo**:
```
Task ID=1: llm_output="Análisis de 50 vendedores..."
  → execution_status = 'executed'
```

### Paso 3: Backfill - Tareas Pendientes

```sql
UPDATE tasks
SET execution_status = 'pending'
WHERE (llm_output IS NULL OR TRIM(llm_output) = '') AND execution_status = 'pending';
```

**Lógica**: Si no tiene output → está pendiente

**Ejemplo**:
```
Task ID=2: llm_output = NULL
  → execution_status = 'pending'
```

---

## Transacciones en Código

### 1. CREATE TASK

```python
# app.py línea ~511-524
INSERT INTO tasks (
    project_id, title, description, task_type, context, status,
    suggested_model, router_summary, llm_output, useful_extract,
    uploads_json, execution_status, created_at, updated_at
)
VALUES (
    ?, ?, ?, ?, ?, 'router_listo',
    '', '', '', '', '[]', 'pending', ?, ?
)

# execution_status = 'pending' automáticamente
```

### 2. EXECUTE TASK → SUCCESS

```python
# app.py línea ~620-624 (update_task_result)
UPDATE tasks
SET llm_output = ?, useful_extract = ?,
    status = 'ejecutado',
    execution_status = 'executed',  ← NUEVO
    updated_at = ?
WHERE id = ?
```

### 3. EXECUTE TASK → PREVIEW

```python
# app.py línea ~2843
execution_status = "preview"
save_execution_result(
    task_id=task_id,
    model_used=model_used,
    router_summary=router_summary,
    llm_output=output,
    useful_extract=extract,
    execution_status=execution_status,  ← NUEVO
    router_metrics=router_metrics,
)
```

### 4. EXECUTE TASK → ERROR

```python
# app.py línea ~2867
execution_status = "failed"
save_execution_result(
    task_id=task_id,
    model_used=model_used,
    router_summary=router_summary,
    llm_output=output,
    useful_extract=extract,
    execution_status=execution_status,  ← NUEVO
    router_metrics=router_metrics,
)
```

### 5. SAVE EXECUTION RESULT

```python
# app.py línea ~603-611
UPDATE tasks
SET suggested_model = ?,
    router_summary = ?,
    llm_output = ?,
    useful_extract = ?,
    status = ?,
    execution_status = ?,  ← NUEVO
    router_metrics_json = ?,
    updated_at = ?
WHERE id = ?

# Parámetros: (..., execution_status, ...)
```

---

## Queries Útiles para Debugging

### Ver todos los estados

```sql
SELECT id, title, execution_status, llm_output, status
FROM tasks
ORDER BY updated_at DESC;
```

### Contar tareas por estado

```sql
SELECT execution_status, COUNT(*) as count
FROM tasks
GROUP BY execution_status;

-- Resultado esperado:
-- pending:  X tareas sin ejecutar
-- executed: Y tareas con resultado
-- preview:  Z tareas demo
-- failed:   W tareas fallidas
```

### Ver tareas recientemente ejecutadas

```sql
SELECT id, title, execution_status, updated_at
FROM tasks
WHERE execution_status = 'executed'
ORDER BY updated_at DESC
LIMIT 10;
```

### Ver tareas fallidas

```sql
SELECT id, title, router_summary, updated_at
FROM tasks
WHERE execution_status = 'failed'
ORDER BY updated_at DESC;
```

### Verificar backfill

```sql
-- Verificar que no hay tareas con output pero execution_status='pending'
SELECT id, title, LENGTH(llm_output) as output_len, execution_status
FROM tasks
WHERE execution_status = 'pending' AND llm_output IS NOT NULL AND TRIM(llm_output) != '';
-- Debe retornar 0 filas

-- Verificar que no hay tareas sin output pero execution_status='executed'
SELECT id, title, execution_status
FROM tasks
WHERE execution_status = 'executed' AND (llm_output IS NULL OR TRIM(llm_output) = '');
-- Debe retornar 0 filas
```

---

## Rollback (Si Necesario)

Si por alguna razón necesitas revertir:

```sql
-- Remover columna (nota: esto borra los datos)
ALTER TABLE tasks DROP COLUMN execution_status;

-- O simplemente no usarla:
-- El código sigue funcionando porque status sigue existiendo
```

**Nota**: No se recomienda rollback. Es mejor mantener la columna (no daña nada).

---

## Verificación Post-Migración

```sql
-- Paso 1: Verificar estructura
PRAGMA table_info(tasks);
-- Debe mostrar execution_status como TEXT

-- Paso 2: Verificar datos
SELECT COUNT(*) as total,
       COUNT(CASE WHEN execution_status='pending' THEN 1 END) as pending,
       COUNT(CASE WHEN execution_status='executed' THEN 1 END) as executed,
       COUNT(CASE WHEN execution_status='preview' THEN 1 END) as preview,
       COUNT(CASE WHEN execution_status='failed' THEN 1 END) as failed
FROM tasks;

-- Paso 3: Verificar que NO hay NULLs
SELECT COUNT(*) as count
FROM tasks
WHERE execution_status IS NULL;
-- Debe retornar 0
```

---

## Performance

### Índices (Opcional)

Si hay muchas tareas, considerar índice:

```sql
CREATE INDEX idx_tasks_execution_status ON tasks(execution_status);
```

**Beneficio**: Queries como "SELECT * FROM tasks WHERE execution_status='executed'" son más rápidas

### No Necesario Si

- < 10,000 tareas
- Las queries no se ejecutan muy frecuentemente
- No tienes performance issues

---

## Notas Importantes

1. **Default Value**: `DEFAULT 'pending'` garantiza que nuevas tareas sin ejecutar tengan el valor correcto

2. **Backfill**: El backfill se ejecuta automáticamente en `init_db()`, es transparente

3. **Compatibilidad**: El campo está en la misma tabla, no requiere cambios en joins

4. **No Destructivo**: La migración NO borra ni modifica datos importantes, solo agrega un campo

5. **Atómico**: Cada actualización de ejecución actualiza explícitamente execution_status

---

**Creado**: 2026-04-18
**Versión**: 1.0
