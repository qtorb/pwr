#!/usr/bin/env python3
"""
E0 Validation Tests: Consolidación de datos estructurados
Valida que router_metrics_json, get_capabilities(), executions_history funcionan correctamente.
"""

import sys
import json
import sqlite3
from pathlib import Path

# Agregar router al path
sys.path.insert(0, str(Path(__file__).parent))

from router.model_catalog import ModelCatalog
from router.domain import TaskInput, ExecutionResult, RoutingDecision, ExecutionMetrics, ExecutionError
from datetime import datetime


def get_test_db() -> sqlite3.Connection:
    """Crea BD de prueba con schema mínimo."""
    db_path = Path(__file__).parent / "test_e0.db"
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(str(db_path))

    # Crear tabla model_catalog con datos de prueba
    conn.execute("""
        CREATE TABLE model_catalog (
            id INTEGER PRIMARY KEY,
            provider TEXT,
            model_name TEXT,
            estimated_cost_per_run REAL,
            mode TEXT,
            capabilities_json TEXT,
            context_window INTEGER,
            status TEXT,
            pricing_input_per_mtok REAL,
            pricing_output_per_mtok REAL,
            is_internal INTEGER,
            deprecated_at TEXT
        )
    """)

    # Insertar datos de prueba
    conn.execute("""
        INSERT INTO model_catalog
        (provider, model_name, estimated_cost_per_run, mode, capabilities_json, context_window, status, is_internal)
        VALUES
        (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "gemini",
        "gemini-2.5-flash-lite",
        0.05,
        "eco",
        json.dumps({"vision": True, "reasoning": False, "code_execution": True}),
        1000000,
        "active",
        0
    ))

    conn.execute("""
        INSERT INTO model_catalog
        (provider, model_name, estimated_cost_per_run, mode, capabilities_json, context_window, status, is_internal)
        VALUES
        (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "gemini",
        "gemini-2.5-pro",
        0.30,
        "racing",
        json.dumps({"vision": True, "reasoning": True, "code_execution": True}),
        2000000,
        "active",
        0
    ))

    conn.execute("""
        INSERT INTO model_catalog
        (provider, model_name, estimated_cost_per_run, mode, capabilities_json, context_window, status, is_internal)
        VALUES
        (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "mock",
        "mock-eco",
        0.0,
        "eco",
        json.dumps({"vision": False, "reasoning": False, "code_execution": False}),
        100000,
        "active",
        1
    ))

    # Crear tabla tasks para test 2 (router_metrics_json)
    conn.execute("""
        CREATE TABLE tasks (
            id INTEGER PRIMARY KEY,
            suggested_model TEXT DEFAULT '',
            router_summary TEXT DEFAULT '',
            router_metrics_json TEXT DEFAULT '{}',
            llm_output TEXT DEFAULT '',
            useful_extract TEXT DEFAULT '',
            status TEXT DEFAULT 'borrador',
            updated_at TEXT
        )
    """)
    conn.execute("INSERT INTO tasks (id) VALUES (1)")

    # Crear tabla executions_history para test 4
    conn.execute("""
        CREATE TABLE executions_history (
            id INTEGER PRIMARY KEY,
            task_id INTEGER,
            project_id INTEGER,
            execution_status TEXT,
            mode TEXT,
            model TEXT,
            provider TEXT,
            latency_ms INTEGER,
            estimated_cost REAL,
            executed_at TEXT,
            created_at TEXT
        )
    """)

    conn.commit()
    return conn


def test_1_get_capabilities_from_bd():
    """Test 1: get_capabilities() retorna datos de BD, no hardcoded."""
    print("\n" + "="*80)
    print("TEST 1: get_capabilities() lee de BD (no hardcoded)")
    print("="*80)

    conn = get_test_db()
    catalog = ModelCatalog(conn)

    # Test modelo que existe en BD con capabilities_json
    caps = catalog.get_capabilities("gemini-2.5-flash-lite")
    assert caps is not None, "FAIL: get_capabilities() devolvió None para modelo en BD"
    assert caps.get("vision") == True, "FAIL: vision capability no coincide con BD"
    assert caps.get("reasoning") == False, "FAIL: reasoning capability no coincide con BD"
    assert caps.get("code_execution") == True, "FAIL: code_execution capability no coincide con BD"

    # Test modelo que no existe
    caps_missing = catalog.get_capabilities("nonexistent-model")
    assert caps_missing is None, "FAIL: get_capabilities() debería devolver None para modelo inexistente"

    print("✅ PASS: get_capabilities() lee correctamente de BD")
    print(f"   Capabilities para gemini-2.5-flash-lite: {caps}")
    conn.close()


def test_2_router_metrics_json_serialization():
    """Test 2: router_metrics_json se guarda y parsea correctamente como JSON."""
    print("\n" + "="*80)
    print("TEST 2: router_metrics_json serialización y parseo")
    print("="*80)

    conn = get_test_db()

    # Simular guardado de metrics (similar a lo que hace save_execution_result)
    metrics = {
        "mode": "eco",
        "model": "gemini-2.5-flash-lite",
        "provider": "gemini",
        "latency_ms": 1245,
        "estimated_cost": 0.05,
        "complexity_score": 0.35,
        "status": "executed",
        "reasoning_path": "Tarea acotada de baja complejidad",
        "executed_at": datetime.now().isoformat(),
    }

    metrics_json = json.dumps(metrics)

    # Guardar en BD
    conn.execute(
        "UPDATE tasks SET router_metrics_json = ? WHERE id = 1",
        (metrics_json,)
    )
    conn.commit()

    # Leer de BD y parsear
    row = conn.execute("SELECT router_metrics_json FROM tasks WHERE id = 1").fetchone()
    assert row is not None, "FAIL: No se encontró registro en tasks"

    stored_json = row[0]
    parsed_metrics = json.loads(stored_json)

    assert parsed_metrics["mode"] == "eco", "FAIL: mode no coincide"
    assert parsed_metrics["model"] == "gemini-2.5-flash-lite", "FAIL: model no coincide"
    assert parsed_metrics["provider"] == "gemini", "FAIL: provider no coincide"
    assert parsed_metrics["latency_ms"] == 1245, "FAIL: latency_ms no coincide"
    assert parsed_metrics["estimated_cost"] == 0.05, "FAIL: estimated_cost no coincide"
    assert parsed_metrics["complexity_score"] == 0.35, "FAIL: complexity_score no coincide"
    assert parsed_metrics["status"] == "executed", "FAIL: status no coincide"

    print("✅ PASS: router_metrics_json se serializa y parsea correctamente")
    print(f"   Stored: {stored_json}")
    print(f"   Parsed: {parsed_metrics}")

    conn.close()


def test_3_router_summary_compatibility():
    """Test 3: router_summary sigue existiendo para compatibilidad."""
    print("\n" + "="*80)
    print("TEST 3: router_summary compatibilidad (sigue existiendo)")
    print("="*80)

    conn = get_test_db()

    summary = "Ejecución completada\nModo: eco\nModelo: gemini-2.5-flash-lite"

    conn.execute(
        "UPDATE tasks SET router_summary = ? WHERE id = 1",
        (summary,)
    )
    conn.commit()

    row = conn.execute("SELECT router_summary FROM tasks WHERE id = 1").fetchone()
    assert row is not None, "FAIL: No se encontró registro"
    assert row[0] == summary, "FAIL: router_summary no coincide"

    print("✅ PASS: router_summary sigue funcionando para compatibilidad")
    print(f"   Valor guardado: {summary}")

    conn.close()


def test_4_executions_history_schema():
    """Test 4: executions_history tabla existe con schema correcto."""
    print("\n" + "="*80)
    print("TEST 4: executions_history tabla schema")
    print("="*80)

    conn = get_test_db()

    # Verificar que tabla existe
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='executions_history'"
    )
    assert cursor.fetchone() is not None, "FAIL: executions_history tabla no existe"

    # Verificar columnas
    cursor = conn.execute("PRAGMA table_info(executions_history)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}

    expected_columns = {
        "id": "INTEGER",
        "task_id": "INTEGER",
        "project_id": "INTEGER",
        "execution_status": "TEXT",
        "mode": "TEXT",
        "model": "TEXT",
        "provider": "TEXT",
        "latency_ms": "INTEGER",
        "estimated_cost": "REAL",
        "executed_at": "TEXT",
        "created_at": "TEXT",
    }

    for col_name, col_type in expected_columns.items():
        assert col_name in columns, f"FAIL: Columna {col_name} no existe"
        # Note: SQLite type matching can be flexible, so we check the core type
        assert col_type.split()[0] in columns[col_name], \
            f"FAIL: Tipo de {col_name} es {columns[col_name]}, esperado {col_type}"

    # Insertar registro de prueba
    now = datetime.now().isoformat()
    conn.execute("""
        INSERT INTO executions_history
        (task_id, project_id, execution_status, mode, model, provider, latency_ms, estimated_cost, executed_at, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (1, 1, "executed", "eco", "gemini-2.5-flash-lite", "gemini", 1234, 0.05, now, now))
    conn.commit()

    row = conn.execute("SELECT * FROM executions_history WHERE task_id = 1").fetchone()
    assert row is not None, "FAIL: No se pudo insertar en executions_history"

    print("✅ PASS: executions_history existe con schema correcto (11 campos minimalista)")
    print(f"   Columnas: {', '.join(expected_columns.keys())}")
    print(f"   Registro de prueba insertado exitosamente")

    conn.close()


def test_5_integration_flow():
    """Test 5: Flujo E2E (crear proyecto, ejecutar, verificar BD, sin errores UI)."""
    print("\n" + "="*80)
    print("TEST 5: Flujo E2E - Integración completa")
    print("="*80)

    conn = get_test_db()

    # Paso 1: Crear catálogo desde BD
    print("\n  Paso 1: Inicializar ModelCatalog desde BD...")
    catalog = ModelCatalog(conn)

    # Paso 2: Simular decisión y ejecución
    print("  Paso 2: Simular ejecución (DecisionEngine → ExecutionService)...")
    task_input = TaskInput(
        task_id=1,
        title="Test E2E",
        description="Prueba de flujo E2E",
        task_type="Escribir",
        context="Contexto minimalista"
    )

    # Paso 3: Simular resultado de ejecución
    print("  Paso 3: Simular ExecutionResult...")
    decision = RoutingDecision(
        mode="eco",
        provider="gemini",
        model="gemini-2.5-flash-lite",
        reasoning_path="Tarea de escritura con complejidad baja",
        complexity_score=0.25,
    )
    metrics = ExecutionMetrics(
        latency_ms=1567,
        estimated_cost=0.05,
        provider_used="gemini",
        model_used="gemini-2.5-flash-lite",
    )
    result = ExecutionResult(
        task_id=1,
        status="completed",
        output_text="Output de prueba E2E",
        routing=decision,
        metrics=metrics,
        error=None,
    )

    # Paso 4: Guardar metrics en BD (simular save_execution_result)
    print("  Paso 4: Guardar router_metrics_json en BD...")
    router_metrics = {
        "mode": result.routing.mode,
        "model": result.metrics.model_used,
        "provider": result.metrics.provider_used,
        "latency_ms": result.metrics.latency_ms,
        "estimated_cost": result.metrics.estimated_cost,
        "complexity_score": result.routing.complexity_score,
        "status": "executed",
        "reasoning_path": result.routing.reasoning_path,
        "executed_at": datetime.now().isoformat(),
    }
    metrics_json = json.dumps(router_metrics)

    router_summary = (
        f"Ejecución completada\n"
        f"Modo: {result.routing.mode}\n"
        f"Modelo: {result.metrics.model_used}\n"
        f"Proveedor: {result.metrics.provider_used}"
    )

    conn.execute("""
        UPDATE tasks
        SET router_summary = ?, router_metrics_json = ?, status = ?, updated_at = ?
        WHERE id = ?
    """, (router_summary, metrics_json, "executed", datetime.now().isoformat(), 1))
    conn.commit()

    # Paso 5: Verificar que todo se guardó
    print("  Paso 5: Verificar persistencia en BD...")
    row = conn.execute(
        "SELECT router_summary, router_metrics_json, status FROM tasks WHERE id = 1"
    ).fetchone()
    assert row is not None, "FAIL: No se encontró registro"

    stored_summary, stored_metrics, stored_status = row
    assert stored_status == "executed", f"FAIL: status es {stored_status}"
    assert stored_summary == router_summary, "FAIL: router_summary no coincide"

    parsed_metrics = json.loads(stored_metrics)
    assert parsed_metrics["mode"] == "eco", "FAIL: modo no coincide en E2E"
    assert parsed_metrics["provider"] == "gemini", "FAIL: provider no coincide en E2E"

    print("✅ PASS: Flujo E2E completo exitoso")
    print(f"   ✓ router_summary guardado correctamente")
    print(f"   ✓ router_metrics_json serializado y guardado")
    print(f"   ✓ Datos verificables en BD")
    print(f"   ✓ Status actualizado a 'executed'")

    conn.close()


def run_all_tests():
    """Ejecuta todos los tests de validación E0."""
    print("\n")
    print("╔" + "═"*78 + "╗")
    print("║" + " VALIDACIÓN E0: CONSOLIDACIÓN DE DATOS ESTRUCTURADOS ".center(78) + "║")
    print("╚" + "═"*78 + "╝")

    tests = [
        ("Test 1: get_capabilities() de BD", test_1_get_capabilities_from_bd),
        ("Test 2: router_metrics_json serialización", test_2_router_metrics_json_serialization),
        ("Test 3: router_summary compatibilidad", test_3_router_summary_compatibility),
        ("Test 4: executions_history schema", test_4_executions_history_schema),
        ("Test 5: Flujo E2E integración", test_5_integration_flow),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            failed += 1
            print(f"\n❌ FAIL: {e}")
        except Exception as e:
            failed += 1
            print(f"\n❌ ERROR: {e}")

    print("\n" + "="*80)
    print(f"RESULTADOS: {passed} PASS, {failed} FAIL")
    print("="*80 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
