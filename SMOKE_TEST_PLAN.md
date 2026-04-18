# SMOKE TEST: 7 Casos Funcionales

**Objetivo**: Validar que execution_status se guarda y lee correctamente en BD

**Plan**: Ejecutar 7 casos reales, verificar estado en BD, capturar pantallas

---

## CASOS A VALIDAR

### CASO 1: Crear Nueva Tarea
**Esperado**: `execution_status = 'pending'`

Pasos:
1. Ir a Home
2. Click [➕ Crear nuevo activo]
3. Llenar formulario: Título="Test: Crear tarea"
4. Click [Crear]
5. **Verificar BD**: SELECT execution_status FROM tasks WHERE title='Test: Crear tarea'
6. **Esperado**: 'pending' ✅

---

### CASO 2: Ejecutar Tarea → Éxito
**Esperado**: `execution_status = 'executed'`

Pasos:
1. En proyecto, crear tarea: "Test: Ejecutar éxito"
2. Click [⚡ Ejecutar ahora]
3. Esperar resultado exitoso
4. **Verificar BD**: SELECT execution_status FROM tasks WHERE title='Test: Ejecutar éxito'
5. **Verificar UI**: render_task_state() muestra "✅ Resultado listo"
6. **Esperado**: BD='executed', UI=correcta ✅

---

### CASO 3: Badge Semántico (Recién Generado)
**Esperado**: `determine_semantic_badge() retorna "🔥 Recién generado"`

Pasos:
1. Ejecutar tarea del CASO 2 (resultado reciente)
2. Ir a Home
3. En sección "Continuar desde aquí" o "Últimos activos"
4. **Verificar**: Badge es "🔥 Recién generado"
5. **Verificar BD**: execution_status='executed' AND updated_at (hace < 1h)
6. **Esperado**: Badge correcto ✅

---

### CASO 4: Ejecutar Tarea → Error
**Esperado**: `execution_status = 'failed'`

Pasos:
1. Crear tarea: "Test: Ejecutar error" con modelo inválido o sin credenciales
2. Click [⚡ Ejecutar ahora]
3. Esperar error
4. **Verificar BD**: SELECT execution_status FROM tasks WHERE title='Test: Ejecutar error'
5. **Verificar UI**: render_task_state() muestra "⚠️ Algo falló"
6. **Esperado**: BD='failed', UI=correcta ✅

---

### CASO 5: Ejecutar Tarea → Preview/Demo
**Esperado**: `execution_status = 'preview'`

Pasos:
1. Crear tarea: "Test: Demo"
2. Click [⚡ Ejecutar ahora] SIN conectar provider real
3. Esperar propuesta demo
4. **Verificar BD**: SELECT execution_status FROM tasks WHERE title='Test: Demo'
5. **Verificar UI**: render_task_state() muestra "📋 Propuesta lista"
6. **Esperado**: BD='preview', UI=correcta ✅

---

### CASO 6: Verificar Backfill (Tareas Antiguas)
**Esperado**: Tareas con output → 'executed', sin output → 'pending'

Pasos:
1. **En BD, verificar tareas creadas ANTES de la migración**:
   ```sql
   SELECT id, title, llm_output, execution_status
   FROM tasks
   LIMIT 10;
   ```
2. **Regla 1**: Si `llm_output IS NOT NULL AND TRIM(llm_output) != ''` → `execution_status` debe ser 'executed'
3. **Regla 2**: Si `llm_output IS NULL OR TRIM(llm_output) = ''` → `execution_status` debe ser 'pending'
4. **Verificar**: NO hay inconsistencias
5. **Esperado**: 100% de tareas correctamente backfilled ✅

---

### CASO 7: Estado Persiste Después de Reload
**Esperado**: Estado en BD es consistente, no importa reloads

Pasos:
1. Ejecutar tarea: "Test: Persistencia"
2. Resultado exitoso → `execution_status = 'executed'`
3. **Ir a Home** (reload completo, limpia session_state)
4. **Abrir tarea nuevamente**
5. **Verificar**: Estado sigue siendo "✅ Resultado listo" (no cambió)
6. **Verificar BD**: `execution_status` sigue siendo 'executed'
7. **Esperado**: Estado persiste, no es volátil ✅

---

## CRITERIOS DE ÉXITO

| Caso | Esperado | Validación |
|------|----------|-----------|
| 1 | pending | SQL: ✓, count=1 |
| 2 | executed | SQL: ✓, UI: ✓, Botones: ✓ |
| 3 | Badge 🔥 | SQL: ✓, Home: ✓ |
| 4 | failed | SQL: ✓, UI: ✓ |
| 5 | preview | SQL: ✓, UI: ✓ |
| 6 | 100% backfill | SQL: 0 inconsistencias |
| 7 | Persiste | SQL: ✓, UI reload: ✓ |

**Criterio de Éxito Global**: 7/7 casos ✅

---

## VALIDACIÓN TÉCNICA

Para cada caso, verificar:

1. **BD está correcta**
   ```sql
   SELECT id, title, execution_status, llm_output, status, updated_at
   FROM tasks
   WHERE id = ?
   ```

2. **UI refleja estado correcto**
   - render_task_state() muestra estado correcto
   - determine_semantic_badge() retorna badge correcto
   - Botones son contextuales

3. **No hay inconsistencias**
   - execution_status vs llm_output
   - execution_status vs status
   - execution_status vs UI mostrada

---

## SETUP

```python
# Para debugging rápido durante tests
import sqlite3

def check_task_state(task_id):
    with sqlite3.connect('data/pwr.db') as conn:
        conn.row_factory = sqlite3.Row
        task = conn.execute(
            "SELECT id, title, execution_status, llm_output, status FROM tasks WHERE id=?",
            (task_id,)
        ).fetchone()
        return dict(task) if task else None

# Uso en test:
# result = check_task_state(1)
# print(f"Execution status: {result['execution_status']}")
```

---

## DOCUMENTACIÓN DE RESULTADOS

Para cada caso:
1. Screenshot de UI (estado mostrado)
2. SQL query result (estado en BD)
3. Verificación: ¿Coinciden?
4. ✅ o ❌

---

**Listo para ejecutar**
