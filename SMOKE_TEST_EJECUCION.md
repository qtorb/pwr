# SMOKE TEST: EJECUCIÓN REAL

**Fecha**: 2026-04-18
**Status**: En progreso
**Objetivo**: Validar 7 casos con pantallas + verificación BD

---

## ESTADO INICIAL (Baseline)

```
✅ BD inicializada
✅ Backfill: 100% consistente (0 inconsistencias)
✅ Tareas en BD: 6 totales
   - 1 ejecutada (execution_status='executed')
   - 5 pendientes (execution_status='pending')
```

---

## CASO 1: Crear Nueva Tarea

### Pasos:
1. Ir a Home → Click [➕ Crear nuevo activo]
2. Formulario:
   - Título: "SMOKE_TEST_01: Create pending"
   - Descripción: "Test case 1"
3. Click [Crear]

### Validación BD:
```sql
SELECT id, title, execution_status FROM tasks WHERE title LIKE '%SMOKE_TEST_01%';
```

**Esperado**: `execution_status = 'pending'` ✅

---

## CASO 2: Ejecutar Tarea → Éxito

### Pasos:
1. En proyecto, encontrar tarea: "SMOKE_TEST_01"
2. Click [⚡ Ejecutar ahora]
3. Esperar resultado exitoso
4. Capturar pantalla mostrando: "✅ Resultado listo"

### Validación BD:
```sql
SELECT id, execution_status, LENGTH(llm_output) as output_len FROM tasks WHERE title LIKE '%SMOKE_TEST_01%';
```

**Esperado**:
- `execution_status = 'executed'` ✅
- `output_len > 0` ✅

---

## CASO 3: Badge Semántico (Recién Generado)

### Pasos:
1. Ir a Home
2. Ver sección "Continuar desde aquí" o "Últimos activos"
3. Buscar tarea del CASO 2
4. Capturar pantalla mostrando badge "🔥 Recién generado"

### Validación BD + UI:
```sql
SELECT execution_status, updated_at FROM tasks WHERE title LIKE '%SMOKE_TEST_01%';
-- Debe ser: execution_status='executed' Y updated_at hace < 1 hora
```

**Esperado**: Badge correcto en Home ✅

---

## CASO 4: Ejecutar Tarea → Error

### Pasos:
1. Crear tarea: "SMOKE_TEST_04: Error test"
2. Click [⚡ Ejecutar ahora]
3. Fuerza error (ej: modelo inválido o sin credenciales)
4. Capturar pantalla mostrando: "⚠️ Algo falló"

### Validación BD:
```sql
SELECT execution_status, router_summary FROM tasks WHERE title LIKE '%SMOKE_TEST_04%';
```

**Esperado**:
- `execution_status = 'failed'` ✅
- `router_summary` contiene "Error" o "fallido"  ✅

---

## CASO 5: Ejecutar Tarea → Preview

### Pasos:
1. Crear tarea: "SMOKE_TEST_05: Preview test"
2. Click [⚡ Ejecutar ahora] SIN provider real
3. Observar fallback a demo
4. Capturar pantalla mostrando: "📋 Propuesta lista"

### Validación BD:
```sql
SELECT execution_status, router_summary FROM tasks WHERE title LIKE '%SMOKE_TEST_05%';
```

**Esperado**:
- `execution_status = 'preview'` ✅
- `router_summary` contiene "Propuesta" o "demo" ✅

---

## CASO 6: Verificar Backfill (Ya Validado)

### Resultado:
```
✅ Tareas con output → execution_status='executed'
✅ Tareas sin output → execution_status='pending'
✅ 0 inconsistencias detectadas
```

---

## CASO 7: Estado Persiste Después de Reload

### Pasos:
1. Ejecutar tarea del CASO 2 (si aún no está ejecutada)
2. Estado debe ser: "✅ Resultado listo"
3. Hacer refresh de página (simular reload)
4. Abrir tarea nuevamente
5. Capturar pantalla
6. Verificar: Estado sigue siendo "✅ Resultado listo"

### Validación BD:
```sql
SELECT execution_status FROM tasks WHERE id = <task_id>;
```

**Esperado**: `execution_status` no cambiado ✅

---

## RESUMEN DE VALIDACIONES

| Caso | Descripción | Esperado | BD | UI | Resultado |
|------|---|---|---|---|---|
| 1 | Crear tarea | pending | ✓ | N/A | 🔄 |
| 2 | Ejecutar éxito | executed | ✓ | "✅ Resultado listo" | 🔄 |
| 3 | Badge semántico | 🔥 Recién gen. | ✓ | Mostrado en Home | 🔄 |
| 4 | Error en ejecución | failed | ✓ | "⚠️ Algo falló" | 🔄 |
| 5 | Preview/demo | preview | ✓ | "📋 Propuesta" | 🔄 |
| 6 | Backfill consistente | 0 inconsist. | ✓ | N/A | ✅ |
| 7 | Persiste reload | mismo estado | ✓ | Mismo UI | 🔄 |

---

## INSTRUCCIONES PARA EJECUTAR

1. **Limpiar BD anterior** (opcional):
   ```bash
   rm pwr_data/pwr.db
   python3 -c "from app import init_db; init_db()"
   ```

2. **Iniciar Streamlit**:
   ```bash
   streamlit run app.py
   ```

3. **Para cada caso**:
   - Navegar por UI según pasos
   - Capturar pantalla si es relevante
   - Ejecutar query de validación
   - Documentar resultado

4. **Helper para BD**:
   ```bash
   python3 test_helper.py find "SMOKE_TEST_01"
   python3 test_helper.py check <task_id>
   python3 test_helper.py backfill
   ```

---

## CRITERIO DE ÉXITO

✅ **Global**: 7/7 casos pasan
- Caso 1-5: BD + UI coherentes
- Caso 6: Backfill 100% consistente
- Caso 7: Estado persistente

Si todas las validaciones pasan → **READY FOR PRODUCTION**
Si alguna falla → **DEBUG Y FIX ANTES DE PRODUCCIÓN**

---

**Pendiente**: Ejecutar casos 1-5 y 7 con Streamlit
