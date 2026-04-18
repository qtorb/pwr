#!/usr/bin/env python3
"""
Helper para validar execution_status durante smoke test
Uso: python test_helper.py <comando> [args]
"""

import sqlite3
from pathlib import Path
import os

# Asegurarse de que estamos en el directorio correcto
os.chdir(Path(__file__).parent)

DB_PATH = Path.cwd() / "pwr_data" / "pwr.db"

def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def check_task(task_id):
    """Retorna estado completo de una tarea"""
    with get_conn() as conn:
        task = conn.execute(
            """
            SELECT id, title, execution_status, llm_output, status, updated_at
            FROM tasks WHERE id = ?
            """,
            (task_id,)
        ).fetchone()
        if task:
            return dict(task)
        return None

def check_task_by_title(title):
    """Retorna tarea por título"""
    with get_conn() as conn:
        task = conn.execute(
            """
            SELECT id, title, execution_status, llm_output, status, updated_at
            FROM tasks WHERE title LIKE ? LIMIT 1
            """,
            (f"%{title}%",)
        ).fetchone()
        if task:
            return dict(task)
        return None

def list_recent_tasks():
    """Lista últimas 5 tareas"""
    with get_conn() as conn:
        tasks = conn.execute(
            """
            SELECT id, title, execution_status, LENGTH(llm_output) as output_len, status, updated_at
            FROM tasks
            ORDER BY updated_at DESC
            LIMIT 5
            """
        ).fetchall()
        return [dict(t) for t in tasks]

def check_backfill():
    """Verifica que backfill es consistente"""
    with get_conn() as conn:
        # Inconsistencias: tiene output pero status='pending'
        inconsistency1 = conn.execute(
            """
            SELECT COUNT(*) as count FROM tasks
            WHERE execution_status = 'pending'
            AND llm_output IS NOT NULL
            AND TRIM(llm_output) != ''
            """
        ).fetchone()['count']

        # Inconsistencias: no tiene output pero status='executed'
        inconsistency2 = conn.execute(
            """
            SELECT COUNT(*) as count FROM tasks
            WHERE execution_status = 'executed'
            AND (llm_output IS NULL OR TRIM(llm_output) = '')
            """
        ).fetchone()['count']

        # Resumen por estado
        summary = conn.execute(
            """
            SELECT execution_status, COUNT(*) as count
            FROM tasks
            GROUP BY execution_status
            """
        ).fetchall()

        return {
            'inconsistency_pending_with_output': inconsistency1,
            'inconsistency_executed_without_output': inconsistency2,
            'summary': {dict(s)['execution_status']: dict(s)['count'] for s in summary}
        }

def print_task(task):
    """Formatea tarea para display"""
    if not task:
        print("❌ Tarea no encontrada")
        return

    print(f"\n📋 Task #{task['id']}: {task['title']}")
    print(f"   execution_status: {task['execution_status']}")
    print(f"   status: {task['status']}")
    print(f"   output_len: {len(task['llm_output']) if task['llm_output'] else 0}")
    print(f"   updated_at: {task['updated_at']}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Comandos disponibles:")
        print("  python test_helper.py check <task_id>")
        print("  python test_helper.py find <title_search>")
        print("  python test_helper.py list")
        print("  python test_helper.py backfill")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "check" and len(sys.argv) > 2:
        task = check_task(int(sys.argv[2]))
        print_task(task)

    elif cmd == "find" and len(sys.argv) > 2:
        title = sys.argv[2]
        task = check_task_by_title(title)
        if task:
            print_task(task)
        else:
            print(f"❌ No encontrada tarea con '{title}'")

    elif cmd == "list":
        print("\n📊 Últimas 5 tareas:")
        tasks = list_recent_tasks()
        for task in tasks:
            print(f"\n  #{task['id']}: {task['title'][:50]}")
            print(f"     execution_status={task['execution_status']}, output_len={task['output_len']}")

    elif cmd == "backfill":
        result = check_backfill()
        print("\n🔍 Validación de Backfill:")
        print(f"   Tareas con output pero execution_status='pending': {result['inconsistency_pending_with_output']}")
        print(f"   Tareas sin output pero execution_status='executed': {result['inconsistency_executed_without_output']}")
        print(f"\n   Resumen por estado:")
        for status, count in result['summary'].items():
            print(f"     {status}: {count}")

        if result['inconsistency_pending_with_output'] == 0 and result['inconsistency_executed_without_output'] == 0:
            print("\n✅ Backfill es 100% consistente")
        else:
            print("\n❌ Hay inconsistencias!")
