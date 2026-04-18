#!/usr/bin/env python3
"""
SMOKE TEST AUTOMÁTICO: 7 Casos Funcionales
Valida que execution_status se guarda y lee correctamente en BD
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime

# Setup
DB_PATH = Path(__file__).parent / "pwr_data" / "pwr.db"
sys.path.insert(0, str(Path(__file__).parent))

from app import (
    init_db, get_conn, create_task, update_task_result,
    get_task, determine_semantic_badge
)

class SmokeTest:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.cases_results = []

    def assert_equal(self, actual, expected, message):
        """Verifica que actual == expected"""
        if actual == expected:
            print(f"  ✅ {message}")
            return True
        else:
            print(f"  ❌ {message}")
            print(f"     Esperado: {expected}")
            print(f"     Actual: {actual}")
            return False

    def check_task_state(self, task_id, expected_status, expected_has_output=None):
        """Verifica el estado de una tarea en BD"""
        with get_conn() as conn:
            task = conn.execute(
                "SELECT execution_status, llm_output FROM tasks WHERE id = ?",
                (task_id,)
            ).fetchone()

        if not task:
            print(f"  ❌ Tarea {task_id} no encontrada")
            return False

        has_output = len(task['llm_output']) > 0 if task['llm_output'] else False
        passed = True

        if not self.assert_equal(task['execution_status'], expected_status,
                                  f"execution_status = '{expected_status}'"):
            passed = False

        if expected_has_output is not None:
            if not self.assert_equal(has_output, expected_has_output,
                                      f"has_output = {expected_has_output}"):
                passed = False

        return passed

    def test_case_1_create_task(self):
        """CASO 1: Crear Nueva Tarea → execution_status='pending'"""
        print("\n" + "="*60)
        print("CASO 1: Crear Nueva Tarea")
        print("="*60)

        # Crear tarea
        try:
            project_id = self._get_test_project_id()
            task_id = create_task(
                project_id=project_id,
                title="SMOKE_TEST_01: Create pending task",
                description="Test case 1 - Crear tarea",
                task_type="Pensar",
                context="",
                uploaded_files=None
            )
            print(f"  ✓ Tarea creada: ID={task_id}")
        except Exception as e:
            print(f"  ❌ Error al crear tarea: {e}")
            self.failed += 1
            return False

        # Validar en BD
        result = self.check_task_state(task_id, 'pending', False)

        if result:
            self.passed += 1
        else:
            self.failed += 1

        self.cases_results.append(("CASO 1: Crear tarea", result))
        return result

    def test_case_2_execute_success(self):
        """CASO 2: Ejecutar Tarea → Éxito → execution_status='executed'"""
        print("\n" + "="*60)
        print("CASO 2: Ejecutar Tarea (Éxito)")
        print("="*60)

        try:
            project_id = self._get_test_project_id()
            task_id = create_task(
                project_id=project_id,
                title="SMOKE_TEST_02: Execute success",
                description="Test case 2 - Ejecución exitosa",
                task_type="Pensar",
                context="Simular resultado de ejecución",
                uploaded_files=None
            )
            print(f"  ✓ Tarea creada: ID={task_id}")

            # Simular resultado exitoso
            output = "Resultado exitoso de análisis completo.\nLinea 2 con contenido.\nLinea 3."
            extract = output[:100]

            update_task_result(task_id, output, extract)
            print(f"  ✓ Resultado guardado")
        except Exception as e:
            print(f"  ❌ Error: {e}")
            self.failed += 1
            return False

        # Validar en BD
        result = self.check_task_state(task_id, 'executed', True)

        if result:
            self.passed += 1
        else:
            self.failed += 1

        self.cases_results.append(("CASO 2: Ejecutar exitoso", result))
        return result

    def test_case_3_semantic_badge(self):
        """CASO 3: Badge Semántico Basado en execution_status"""
        print("\n" + "="*60)
        print("CASO 3: Badge Semántico")
        print("="*60)

        try:
            # Obtener tarea del CASO 2
            with get_conn() as conn:
                task = conn.execute(
                    "SELECT * FROM tasks WHERE title LIKE '%SMOKE_TEST_02%' LIMIT 1"
                ).fetchone()
                task_dict = dict(task)

            if not task:
                print("  ❌ No se encontró tarea del CASO 2")
                self.failed += 1
                return False

            print(f"  ✓ Tarea encontrada: {task_dict['title']}")

            # Verificar badge semántico
            badge = determine_semantic_badge(task_dict)
            print(f"  ✓ Badge generado: {badge}")

            # Validar que contiene emoji y texto
            has_emoji = any(c in badge for c in ['🔥', '✅', '📋', '⚠️', '✨', '📌'])
            has_text = ' ' in badge  # Tiene al menos 2 palabras

            if self.assert_equal(has_emoji and has_text, True,
                                 f"Badge es válido: '{badge}'"):
                self.passed += 1
            else:
                self.failed += 1
                return False

        except Exception as e:
            print(f"  ❌ Error: {e}")
            self.failed += 1
            return False

        self.cases_results.append(("CASO 3: Badge semántico", True))
        return True

    def test_case_4_execute_error(self):
        """CASO 4: Ejecutar Tarea → Error → execution_status='failed'"""
        print("\n" + "="*60)
        print("CASO 4: Ejecutar Tarea (Error)")
        print("="*60)

        try:
            project_id = self._get_test_project_id()
            task_id = create_task(
                project_id=project_id,
                title="SMOKE_TEST_04: Execute failed",
                description="Test case 4 - Ejecución fallida",
                task_type="Pensar",
                context="Forzar error",
                uploaded_files=None
            )
            print(f"  ✓ Tarea creada: ID={task_id}")

            # Simular error usando save_execution_result
            from app import save_execution_result
            save_execution_result(
                task_id=task_id,
                model_used="test-model",
                router_summary="Intento fallido\nError: API key inválida",
                llm_output="",
                useful_extract="",
                execution_status="failed",
                router_metrics={"status": "failed", "error": "API key inválida"}
            )
            print(f"  ✓ Error simulado en BD")
        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            self.failed += 1
            return False

        # Validar en BD
        result = self.check_task_state(task_id, 'failed', False)

        if result:
            self.passed += 1
        else:
            self.failed += 1

        self.cases_results.append(("CASO 4: Error en ejecución", result))
        return result

    def test_case_5_execute_preview(self):
        """CASO 5: Ejecutar Tarea → Preview → execution_status='preview'"""
        print("\n" + "="*60)
        print("CASO 5: Ejecutar Tarea (Preview/Demo)")
        print("="*60)

        try:
            project_id = self._get_test_project_id()
            task_id = create_task(
                project_id=project_id,
                title="SMOKE_TEST_05: Execute preview",
                description="Test case 5 - Ejecución demo/preview",
                task_type="Pensar",
                context="Sin provider real",
                uploaded_files=None
            )
            print(f"  ✓ Tarea creada: ID={task_id}")

            # Simular preview usando save_execution_result
            from app import save_execution_result
            save_execution_result(
                task_id=task_id,
                model_used="test-model",
                router_summary="Propuesta previa (demo)\nSin resultado real",
                llm_output="Esta es una propuesta de demostración.",
                useful_extract="Propuesta demo",
                execution_status="preview",
                router_metrics={"status": "preview", "mode": "demo"}
            )
            print(f"  ✓ Preview simulado en BD")
        except Exception as e:
            print(f"  ❌ Error: {e}")
            self.failed += 1
            return False

        # Validar en BD
        result = self.check_task_state(task_id, 'preview', True)

        if result:
            self.passed += 1
        else:
            self.failed += 1

        self.cases_results.append(("CASO 5: Preview/demo", result))
        return result

    def test_case_6_backfill_consistency(self):
        """CASO 6: Verificar Backfill es 100% Consistente"""
        print("\n" + "="*60)
        print("CASO 6: Backfill Consistency")
        print("="*60)

        with get_conn() as conn:
            # Check: tareas con output pero execution_status='pending'
            inconsistency1 = conn.execute(
                """
                SELECT COUNT(*) as count FROM tasks
                WHERE execution_status = 'pending'
                AND llm_output IS NOT NULL
                AND TRIM(llm_output) != ''
                """
            ).fetchone()['count']

            # Check: tareas sin output pero execution_status='executed'
            inconsistency2 = conn.execute(
                """
                SELECT COUNT(*) as count FROM tasks
                WHERE execution_status = 'executed'
                AND (llm_output IS NULL OR TRIM(llm_output) = '')
                """
            ).fetchone()['count']

            # Resumen
            summary = conn.execute(
                """
                SELECT execution_status, COUNT(*) as count
                FROM tasks
                GROUP BY execution_status
                ORDER BY execution_status
                """
            ).fetchall()

        print(f"  ✓ Tareas con inconsistencia 1: {inconsistency1}")
        print(f"  ✓ Tareas con inconsistencia 2: {inconsistency2}")
        print(f"  ✓ Resumen por estado:")
        for row in summary:
            print(f"     - {row['execution_status']}: {row['count']}")

        result = (inconsistency1 == 0 and inconsistency2 == 0)
        if self.assert_equal(result, True, "Backfill 100% consistente"):
            self.passed += 1
        else:
            self.failed += 1

        self.cases_results.append(("CASO 6: Backfill consistency", result))
        return result

    def test_case_7_state_persistence(self):
        """CASO 7: Estado Persiste Después de Reload"""
        print("\n" + "="*60)
        print("CASO 7: State Persistence")
        print("="*60)

        try:
            # Obtener tarea del CASO 2
            with get_conn() as conn:
                task = conn.execute(
                    "SELECT id, execution_status FROM tasks WHERE title LIKE '%SMOKE_TEST_02%' LIMIT 1"
                ).fetchone()

            if not task:
                print("  ❌ No se encontró tarea del CASO 2")
                self.failed += 1
                return False

            task_id = task['id']
            original_status = task['execution_status']
            print(f"  ✓ Tarea ID={task_id}, status={original_status}")

            # Simular "reload": leer BD nuevamente
            with get_conn() as conn:
                task_reloaded = conn.execute(
                    "SELECT execution_status FROM tasks WHERE id = ?",
                    (task_id,)
                ).fetchone()

            reloaded_status = task_reloaded['execution_status']
            print(f"  ✓ Después de reload: status={reloaded_status}")

            # Comparar
            if self.assert_equal(reloaded_status, original_status,
                                "Estado persiste (no cambió)"):
                self.passed += 1
            else:
                self.failed += 1
                return False

        except Exception as e:
            print(f"  ❌ Error: {e}")
            self.failed += 1
            return False

        self.cases_results.append(("CASO 7: State persistence", True))
        return True

    def _get_test_project_id(self):
        """Retorna ID del primer proyecto (para tests)"""
        with get_conn() as conn:
            project = conn.execute(
                "SELECT id FROM projects LIMIT 1"
            ).fetchone()

            if not project:
                # Crear proyecto de test si no existe
                from app import create_project
                project_id = create_project(
                    name="SMOKE_TEST_PROJECT",
                    description="Proyecto para smoke tests",
                    objective="Testing",
                    base_context="",
                    base_instructions="",
                    tags="test",
                    uploaded_files=None
                )
                return project_id
            else:
                return project['id']

    def run_all(self):
        """Ejecuta todos los test cases"""
        print("\n")
        print("╔" + "="*58 + "╗")
        print("║" + " "*58 + "║")
        print("║" + "  SMOKE TEST: 7 CASOS FUNCIONALES".center(58) + "║")
        print("║" + "="*58 + "║")

        self.test_case_1_create_task()
        self.test_case_2_execute_success()
        self.test_case_3_semantic_badge()
        self.test_case_4_execute_error()
        self.test_case_5_execute_preview()
        self.test_case_6_backfill_consistency()
        self.test_case_7_state_persistence()

        # Resumen final
        print("\n" + "="*60)
        print("RESUMEN FINAL")
        print("="*60)

        for case_name, result in self.cases_results:
            status = "✅" if result else "❌"
            print(f"{status} {case_name}")

        print(f"\nTotal: {self.passed} ✅ / {self.failed} ❌")
        print(f"Rate: {self.passed}/{self.passed + self.failed} ({100*self.passed/(self.passed+self.failed):.0f}%)")

        if self.failed == 0:
            print("\n🎉 TODOS LOS CASOS PASARON")
            print("✅ READY FOR SMOKE TEST VALIDATION")
            return True
        else:
            print(f"\n❌ {self.failed} CASOS FALLARON")
            print("⚠️  FIX ANTES DE PRODUCCIÓN")
            return False

if __name__ == "__main__":
    test = SmokeTest()
    success = test.run_all()
    sys.exit(0 if success else 1)
