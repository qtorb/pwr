#!/usr/bin/env python3
"""
E1 SNAPSHOT VALIDATION TESTS

Valida que:
1. build_radar_snapshot() genera JSON válido y consistente
2. Filtra correctly is_internal modelos
3. Incluye todos los campos requeridos
4. Estructura matches BD real
5. Metadata es clara y no confusa
"""

import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime

# Agregar ruta del proyecto
sys.path.insert(0, str(Path(__file__).parent))

# Importar funciones desde app.py
from app import build_radar_snapshot, get_conn, init_db


def test_1_snapshot_status_ok():
    """Test 1: build_radar_snapshot() retorna status ok con BD real."""
    print("\n" + "="*80)
    print("TEST 1: build_radar_snapshot() retorna status ok")
    print("="*80)

    snapshot = build_radar_snapshot(internal=False)

    assert snapshot is not None, "FAIL: Snapshot is None"
    assert "status" in snapshot, "FAIL: 'status' field missing"
    assert snapshot["status"] == "ok", f"FAIL: status is {snapshot['status']}, expected 'ok'"
    assert "radar" in snapshot, "FAIL: 'radar' field missing"
    assert "metadata" in snapshot, "FAIL: 'metadata' field missing"

    print("✅ PASS: Snapshot structure is valid")
    print(f"   Status: {snapshot['status']}")
    print(f"   Keys: {list(snapshot.keys())}")


def test_2_snapshot_json_serializable():
    """Test 2: Snapshot es JSON serializable (sin objetos custom)."""
    print("\n" + "="*80)
    print("TEST 2: Snapshot JSON serializable")
    print("="*80)

    snapshot = build_radar_snapshot(internal=False)

    try:
        json_str = json.dumps(snapshot)
        parsed = json.loads(json_str)
        assert parsed == snapshot, "FAIL: Parsed snapshot doesn't match original"
        print("✅ PASS: Snapshot is fully JSON serializable")
        print(f"   JSON size: {len(json_str)} bytes")
    except (TypeError, json.JSONDecodeError) as e:
        print(f"❌ FAIL: {e}")
        raise


def test_3_filter_internal_false():
    """Test 3: internal=False filtra modelos con is_internal=1."""
    print("\n" + "="*80)
    print("TEST 3: Filter internal=False hides is_internal=1")
    print("="*80)

    snapshot_public = build_radar_snapshot(internal=False)
    radar = snapshot_public["radar"]

    # Verificar que no hay modelos con is_internal=1
    internal_models = []
    for provider_models in radar["providers"].values():
        for model in provider_models.get("models", []):
            if model.get("is_internal") == 1:
                internal_models.append(model["name"])

    assert len(internal_models) == 0, f"FAIL: Found internal models: {internal_models}"
    print(f"✅ PASS: No internal models in public snapshot")
    print(f"   Total models visible: {radar['summary']['total_models']}")


def test_4_include_internal_true():
    """Test 4: internal=True incluye modelos con is_internal=1."""
    print("\n" + "="*80)
    print("TEST 4: Filter internal=True includes is_internal=1")
    print("="*80)

    snapshot_internal = build_radar_snapshot(internal=True)
    radar = snapshot_internal["radar"]

    # Verificar que hay al menos un modelo con is_internal=1
    internal_models = []
    for provider_models in radar["providers"].values():
        for model in provider_models.get("models", []):
            if model.get("is_internal") == 1:
                internal_models.append(model["name"])

    assert len(internal_models) > 0, "FAIL: No internal models found with internal=True"
    print(f"✅ PASS: Internal models included")
    print(f"   Internal models: {', '.join(internal_models)}")
    print(f"   Total models with internals: {radar['summary']['total_models']}")


def test_5_required_fields():
    """Test 5: Todos los modelos tienen campos requeridos."""
    print("\n" + "="*80)
    print("TEST 5: Required fields present in all models")
    print("="*80)

    snapshot = build_radar_snapshot(internal=False)
    radar = snapshot["radar"]

    required_fields = [
        "id", "name", "provider", "mode", "status", "is_internal",
        "estimated_cost_per_run", "context_window", "capabilities"
    ]

    missing_count = 0
    for provider_models in radar["providers"].values():
        for model in provider_models.get("models", []):
            for field in required_fields:
                if field not in model:
                    print(f"   Missing field '{field}' in model {model.get('name', 'UNKNOWN')}")
                    missing_count += 1

    assert missing_count == 0, f"FAIL: {missing_count} missing fields found"
    print(f"✅ PASS: All required fields present")
    print(f"   Fields per model: {', '.join(required_fields)}")


def test_6_capabilities_structure():
    """Test 6: Capabilities es dict válido con estructura esperada."""
    print("\n" + "="*80)
    print("TEST 6: Capabilities structure and content")
    print("="*80)

    snapshot = build_radar_snapshot(internal=False)
    radar = snapshot["radar"]

    capability_stats = {
        "with_vision": 0,
        "with_reasoning": 0,
        "with_code_execution": 0,
        "empty": 0
    }

    for provider_models in radar["providers"].values():
        for model in provider_models.get("models", []):
            caps = model.get("capabilities", {})
            assert isinstance(caps, dict), f"FAIL: capabilities is not dict for {model['name']}"

            if caps.get("vision"):
                capability_stats["with_vision"] += 1
            if caps.get("reasoning"):
                capability_stats["with_reasoning"] += 1
            if caps.get("code_execution"):
                capability_stats["with_code_execution"] += 1
            if not caps:
                capability_stats["empty"] += 1

    print(f"✅ PASS: Capabilities structure valid")
    print(f"   Stats:")
    for key, count in capability_stats.items():
        print(f"      {key}: {count}")


def test_7_consistency_with_db():
    """Test 7: Snapshot es consistente con BD real."""
    print("\n" + "="*80)
    print("TEST 7: Consistency with actual database")
    print("="*80)

    snapshot = build_radar_snapshot(internal=False)
    radar = snapshot["radar"]

    # Query BD directamente
    with get_conn() as conn:
        cursor = conn.execute(
            "SELECT COUNT(*) FROM model_catalog WHERE status='active' AND is_internal=0"
        )
        db_count = cursor.fetchone()[0]

    snapshot_count = radar["summary"]["total_models"]

    assert snapshot_count == db_count, (
        f"FAIL: Snapshot count ({snapshot_count}) != DB count ({db_count})"
    )

    print(f"✅ PASS: Snapshot count matches DB")
    print(f"   DB models (active, public): {db_count}")
    print(f"   Snapshot models: {snapshot_count}")


def test_8_metadata_framing():
    """Test 8: Metadata tiene framing claro (NOT confuso)."""
    print("\n" + "="*80)
    print("TEST 8: Metadata framing clarity")
    print("="*80)

    snapshot = build_radar_snapshot(internal=False)
    metadata = snapshot["metadata"]

    # Verificar que framing es explícito
    required_meta_fields = [
        "generated_at", "radar_version", "catalog_source",
        "framing", "note", "include_internal"
    ]

    missing = [f for f in required_meta_fields if f not in metadata]
    assert len(missing) == 0, f"FAIL: Missing metadata fields: {missing}"

    # Verificar que framing menciona explícitamente lo que NO es
    framing = metadata.get("framing", "")
    assert "NOT observatorio histórico" in framing, "FAIL: Framing doesn't mention NOT historical"
    assert "NOT benchmarking" in framing, "FAIL: Framing doesn't mention NOT benchmarking"
    assert "NOT health monitor" in framing, "FAIL: Framing doesn't mention NOT health monitor"

    print(f"✅ PASS: Metadata has clear framing")
    print(f"   Framing: {framing[:80]}...")
    print(f"   Note: {metadata['note']}")


def test_9_modes_match_models():
    """Test 9: Modelos en 'modes' coinciden con modelos en 'providers'."""
    print("\n" + "="*80)
    print("TEST 9: Modes model lists match providers")
    print("="*80)

    snapshot = build_radar_snapshot(internal=False)
    radar = snapshot["radar"]

    # Recolectar todos los modelos por fuente
    provider_models = set()
    for provider_data in radar["providers"].values():
        for model in provider_data.get("models", []):
            provider_models.add(model["name"])

    # Recolectar todos los modelos desde modes
    mode_models = set()
    for mode_data in radar["modes"].values():
        mode_models.update(mode_data.get("models", []))

    # Deben ser idénticos
    assert provider_models == mode_models, (
        f"FAIL: Model sets don't match\n"
        f"  Only in providers: {provider_models - mode_models}\n"
        f"  Only in modes: {mode_models - provider_models}"
    )

    print(f"✅ PASS: Modes and providers model lists are consistent")
    print(f"   Total models: {len(provider_models)}")


def test_10_e2e_reutilizable():
    """Test 10: Snapshot es reutilizable (mismo output para mismo input)."""
    print("\n" + "="*80)
    print("TEST 10: Snapshot determinism (same input = same output)")
    print("="*80)

    snapshot1 = build_radar_snapshot(internal=False)
    snapshot2 = build_radar_snapshot(internal=False)

    # El radar debe ser idéntico (solo metadata.generated_at puede variar)
    assert snapshot1["status"] == snapshot2["status"], "FAIL: Status differs"
    assert snapshot1["radar"] == snapshot2["radar"], "FAIL: Radar data differs"
    assert snapshot1["metadata"]["radar_version"] == snapshot2["metadata"]["radar_version"], "FAIL: Version differs"

    print(f"✅ PASS: Snapshot is deterministic")
    print(f"   Generated at T1: {snapshot1['metadata']['generated_at']}")
    print(f"   Generated at T2: {snapshot2['metadata']['generated_at']}")
    print(f"   Same radar: {snapshot1['radar'] == snapshot2['radar']}")


def run_all_tests():
    """Ejecuta todos los tests."""
    # Inicializar BD con schema correcto
    init_db()

    print("\n")
    print("╔" + "═"*78 + "╗")
    print("║" + " E1 SNAPSHOT VALIDATION ".center(78) + "║")
    print("╚" + "═"*78 + "╝")

    tests = [
        ("Test 1: Snapshot status ok", test_1_snapshot_status_ok),
        ("Test 2: JSON serializable", test_2_snapshot_json_serializable),
        ("Test 3: Filter internal=False", test_3_filter_internal_false),
        ("Test 4: Include internal=True", test_4_include_internal_true),
        ("Test 5: Required fields", test_5_required_fields),
        ("Test 6: Capabilities structure", test_6_capabilities_structure),
        ("Test 7: Consistency with DB", test_7_consistency_with_db),
        ("Test 8: Metadata framing", test_8_metadata_framing),
        ("Test 9: Modes match models", test_9_modes_match_models),
        ("Test 10: Determinism", test_10_e2e_reutilizable),
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
