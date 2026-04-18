import json
import mimetypes
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

import streamlit as st

APP_TITLE = "Portable Work Router"
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "pwr_data"
PROJECTS_DIR = DATA_DIR / "projects"
TASKS_DIR = DATA_DIR / "tasks"
ASSETS_DIR = DATA_DIR / "assets"
UPLOADS_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "pwr.db"

TIPOS_TAREA = {
    "Pensar": "Exploración, framing o análisis general",
    "Escribir": "Redacción estructurada, narrativa o contenido",
    "Programar": "Código, debugging o implementación técnica",
    "Revisar": "Crítica, QA, evaluación o corrección",
    "Decidir": "Comparar opciones, priorizar o elegir",
}
ESTADOS_TAREA = ["borrador", "router_listo", "ejecutado", "archivado"]
PASOS = ["Tarea", "Router", "Prompt", "Resultado", "Activo"]


def ensure_dirs() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    PROJECTS_DIR.mkdir(exist_ok=True)
    TASKS_DIR.mkdir(exist_ok=True)
    ASSETS_DIR.mkdir(exist_ok=True)
    UPLOADS_DIR.mkdir(exist_ok=True)


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    ensure_dirs()
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                slug TEXT NOT NULL UNIQUE,
                description TEXT DEFAULT '',
                objective TEXT DEFAULT '',
                status TEXT DEFAULT 'activo',
                default_language TEXT DEFAULT 'castellano',
                default_models_json TEXT DEFAULT '{}',
                base_context TEXT DEFAULT '',
                base_instructions TEXT DEFAULT '',
                tags_json TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS project_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                mime_type TEXT DEFAULT '',
                size_bytes INTEGER DEFAULT 0,
                document_role TEXT DEFAULT 'referencia',
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS subprojects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                objective TEXT DEFAULT '',
                status TEXT DEFAULT 'activo',
                inherit_project_context INTEGER DEFAULT 1,
                inherit_project_documents INTEGER DEFAULT 1,
                local_context TEXT DEFAULT '',
                local_instructions TEXT DEFAULT '',
                tags_json TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                subproject_id INTEGER,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                task_type TEXT NOT NULL,
                status TEXT DEFAULT 'borrador',
                tags TEXT DEFAULT '',
                context TEXT DEFAULT '',
                uploads_json TEXT DEFAULT '[]',
                suggested_model TEXT DEFAULT '',
                router_summary TEXT DEFAULT '',
                router_data_json TEXT DEFAULT '',
                prompt_main TEXT DEFAULT '',
                prompt_system TEXT DEFAULT '',
                llm_output TEXT DEFAULT '',
                useful_extract TEXT DEFAULT '',
                markdown_path TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id),
                FOREIGN KEY(subproject_id) REFERENCES subprojects(id)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                subproject_id INTEGER,
                task_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                summary TEXT DEFAULT '',
                content TEXT NOT NULL,
                markdown_path TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id),
                FOREIGN KEY(subproject_id) REFERENCES subprojects(id),
                FOREIGN KEY(task_id) REFERENCES tasks(id)
            )
            """
        )

        task_cols = [row["name"] for row in conn.execute("PRAGMA table_info(tasks)").fetchall()]
        for col, sql in {
            "project_id": "ALTER TABLE tasks ADD COLUMN project_id INTEGER",
            "subproject_id": "ALTER TABLE tasks ADD COLUMN subproject_id INTEGER",
            "uploads_json": "ALTER TABLE tasks ADD COLUMN uploads_json TEXT DEFAULT '[]'",
            "router_summary": "ALTER TABLE tasks ADD COLUMN router_summary TEXT DEFAULT ''",
            "router_data_json": "ALTER TABLE tasks ADD COLUMN router_data_json TEXT DEFAULT ''",
            "prompt_main": "ALTER TABLE tasks ADD COLUMN prompt_main TEXT DEFAULT ''",
            "prompt_system": "ALTER TABLE tasks ADD COLUMN prompt_system TEXT DEFAULT ''",
        }.items():
            if col not in task_cols:
                conn.execute(sql)

        asset_cols = [row["name"] for row in conn.execute("PRAGMA table_info(assets)").fetchall()]
        for col, sql in {
            "project_id": "ALTER TABLE assets ADD COLUMN project_id INTEGER",
            "subproject_id": "ALTER TABLE assets ADD COLUMN subproject_id INTEGER",
        }.items():
            if col not in asset_cols:
                conn.execute(sql)


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def slugify(text: str) -> str:
    safe = "".join(ch.lower() if ch.isalnum() else "-" for ch in text.strip())
    while "--" in safe:
        safe = safe.replace("--", "-")
    return safe.strip("-")[:80] or "item"


def safe_json_loads(value: str, default):
    try:
        return json.loads(value) if value else default
    except Exception:
        return default


def human_size(num_bytes: int) -> str:
    if num_bytes < 1024:
        return f"{num_bytes} B"
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    return f"{num_bytes / (1024 * 1024):.1f} MB"


def task_markdown_path(task_id: int, title: str) -> Path:
    return TASKS_DIR / f"{task_id:04d}-{slugify(title)}.md"


def asset_markdown_path(asset_id: int, title: str) -> Path:
    return ASSETS_DIR / f"{asset_id:04d}-{slugify(title)}.md"


def project_upload_dir(project_id: int) -> Path:
    path = UPLOADS_DIR / f"project_{project_id:04d}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_project_files(project_id: int, files) -> List[Dict]:
    saved = []
    dest = project_upload_dir(project_id)
    for f in files or []:
        name = Path(f.name).name
        target = dest / name
        target.write_bytes(f.getbuffer())
        saved.append(
            {
                "name": name,
                "path": str(target),
                "size": len(f.getbuffer()),
                "mime_type": f.type or mimetypes.guess_type(name)[0] or "application/octet-stream",
            }
        )
    return saved


def save_task_files(project_id: int, task_id: int, files) -> List[Dict]:
    task_dir = project_upload_dir(project_id) / f"task_{task_id:04d}"
    task_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for f in files or []:
        name = Path(f.name).name
        target = task_dir / name
        target.write_bytes(f.getbuffer())
        saved.append(
            {
                "name": name,
                "path": str(target),
                "size": len(f.getbuffer()),
                "mime_type": f.type or mimetypes.guess_type(name)[0] or "application/octet-stream",
            }
        )
    return saved


def create_project(name: str, description: str, objective: str, base_context: str, base_instructions: str, tags: str, uploaded_files) -> int:
    created_at = now_iso()
    slug = slugify(name)
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO projects (
                name, slug, description, objective, status, default_language,
                default_models_json, base_context, base_instructions, tags_json,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, 'activo', 'castellano', '{}', ?, ?, ?, ?, ?)
            """,
            (
                name.strip(), slug, description.strip(), objective.strip(),
                base_context.strip(), base_instructions.strip(),
                json.dumps([t.strip() for t in tags.split(",") if t.strip()], ensure_ascii=False),
                created_at, created_at,
            ),
        )
        project_id = int(cur.lastrowid)

        saved_files = save_project_files(project_id, uploaded_files)
        for item in saved_files:
            conn.execute(
                """
                INSERT INTO project_documents (
                    project_id, title, file_name, file_path, mime_type, size_bytes,
                    document_role, notes, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, 'referencia', '', ?, ?)
                """,
                (
                    project_id, item["name"], item["name"], item["path"], item["mime_type"],
                    item["size"], created_at, created_at,
                ),
            )
    return project_id


def update_project(project_id: int, name: str, description: str, objective: str, base_context: str, base_instructions: str, tags: str) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE projects
            SET name = ?, description = ?, objective = ?, base_context = ?, base_instructions = ?,
                tags_json = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                name.strip(), description.strip(), objective.strip(),
                base_context.strip(), base_instructions.strip(),
                json.dumps([t.strip() for t in tags.split(",") if t.strip()], ensure_ascii=False),
                now_iso(), project_id,
            ),
        )


def create_subproject(project_id: int, name: str, description: str, objective: str, inherit_project_context: bool, inherit_project_documents: bool, local_context: str, local_instructions: str, tags: str) -> int:
    created_at = now_iso()
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO subprojects (
                project_id, name, description, objective, status,
                inherit_project_context, inherit_project_documents,
                local_context, local_instructions, tags_json, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, 'activo', ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project_id, name.strip(), description.strip(), objective.strip(),
                1 if inherit_project_context else 0,
                1 if inherit_project_documents else 0,
                local_context.strip(), local_instructions.strip(),
                json.dumps([t.strip() for t in tags.split(",") if t.strip()], ensure_ascii=False),
                created_at, created_at,
            ),
        )
        return int(cur.lastrowid)


def get_projects() -> List[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT p.*,
                   (SELECT COUNT(*) FROM tasks t WHERE t.project_id = p.id AND t.status != 'archivado') AS task_count,
                   (SELECT COUNT(*) FROM assets a WHERE a.project_id = p.id) AS asset_count,
                   (SELECT COUNT(*) FROM subprojects s WHERE s.project_id = p.id AND s.status = 'activo') AS subproject_count
            FROM projects p
            ORDER BY p.updated_at DESC, p.id DESC
            """
        ).fetchall()


def get_project(project_id: int) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()


def get_project_documents(project_id: int) -> List[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM project_documents WHERE project_id = ? ORDER BY updated_at DESC, id DESC",
            (project_id,),
        ).fetchall()


def get_subprojects(project_id: int) -> List[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT s.*,
                   (SELECT COUNT(*) FROM tasks t WHERE t.subproject_id = s.id AND t.status != 'archivado') AS task_count,
                   (SELECT COUNT(*) FROM assets a WHERE a.subproject_id = s.id) AS asset_count
            FROM subprojects s
            WHERE s.project_id = ?
            ORDER BY s.updated_at DESC, s.id DESC
            """,
            (project_id,),
        ).fetchall()


def get_subproject(subproject_id: Optional[int]) -> Optional[sqlite3.Row]:
    if not subproject_id:
        return None
    with get_conn() as conn:
        return conn.execute("SELECT * FROM subprojects WHERE id = ?", (subproject_id,)).fetchone()


def effective_project_context(project: sqlite3.Row, subproject: Optional[sqlite3.Row]) -> str:
    parts = []
    if subproject and subproject["inherit_project_context"]:
        if project["base_context"]:
            parts.append(project["base_context"])
    elif not subproject:
        if project["base_context"]:
            parts.append(project["base_context"])

    if subproject and subproject["local_context"]:
        parts.append(subproject["local_context"])
    return "\n\n".join([p for p in parts if p.strip()])


def effective_project_instructions(project: sqlite3.Row, subproject: Optional[sqlite3.Row]) -> str:
    parts = []
    if subproject and subproject["inherit_project_context"]:
        if project["base_instructions"]:
            parts.append(project["base_instructions"])
    elif not subproject:
        if project["base_instructions"]:
            parts.append(project["base_instructions"])
    if subproject and subproject["local_instructions"]:
        parts.append(subproject["local_instructions"])
    return "\n\n".join([p for p in parts if p.strip()])


def effective_project_documents(project_docs: List[sqlite3.Row], subproject: Optional[sqlite3.Row]) -> List[sqlite3.Row]:
    if not subproject:
        return project_docs
    if subproject["inherit_project_documents"]:
        return project_docs
    return []


def score_model(task_type: str, title: str, description: str, task_context: str, inherited_context: str, inherited_docs: List[sqlite3.Row], task_uploads: List[Dict]) -> Dict:
    text = f"{title} {description} {task_context} {inherited_context}".lower()
    scores = {"Claude Sonnet": 0, "ChatGPT": 0, "Codex": 0, "Gemini": 0}
    signals = []

    def add(model: str, points: int, reason: str, metric: str):
        scores[model] += points
        signals.append({"model": model, "points": points, "reason": reason, "metric": metric})

    if task_type == "Escribir":
        add("Claude Sonnet", 5, "La tarea exige redacción estructurada, claridad y organización.", "estructura")
        add("ChatGPT", 2, "Puede desbloquear variantes y exploración rápida.", "velocidad")
    elif task_type == "Pensar":
        add("ChatGPT", 4, "La tarea parece de exploración amplia o framing inicial.", "exploración")
        add("Claude Sonnet", 3, "Ayuda a ordenar una reflexión con más estructura.", "profundidad")
    elif task_type == "Programar":
        add("Codex", 7, "La tarea está orientada a código, debugging o implementación.", "código")
        add("ChatGPT", 1, "Puede apoyar como contraste rápido.", "apoyo")
    elif task_type == "Revisar":
        add("Claude Sonnet", 4, "La revisión se beneficia de lectura atenta y respuesta cuidada.", "revisión")
        add("ChatGPT", 2, "Puede servir como contraste y resumen rápido.", "contraste")
    elif task_type == "Decidir":
        add("ChatGPT", 4, "Conviene comparar opciones y avanzar con agilidad.", "decisión")
        add("Claude Sonnet", 2, "Puede ordenar mejor trade-offs complejos.", "trade_offs")

    total_context_len = len((task_context or "").strip()) + len((inherited_context or "").strip())
    if total_context_len > 400:
        add("Claude Sonnet", 2, "Hay bastante contexto heredado y conviene priorizar profundidad.", "contexto")
    if total_context_len > 1000:
        add("Claude Sonnet", 2, "El volumen de contexto es alto y penaliza una lectura superficial.", "contexto_extenso")

    if inherited_docs:
        add("Claude Sonnet", 2, "La tarea hereda documentación estable de proyecto o subproyecto.", "documentación_heredada")
    if task_uploads:
        add("Claude Sonnet", 2, "La tarea incorpora documentos específicos y conviene una lectura estructurada.", "documentos_tarea")
        add("Gemini", 1, "Puede servir como segunda lectura o contraste documental.", "contraste_documental")

    strategic_terms = ["estrateg", "marca", "mensaje", "narrativa", "posicion", "editorial", "roadmap", "stakeholder"]
    if any(k in text for k in strategic_terms):
        add("Claude Sonnet", 2, "Aparece una capa estratégica o editorial relevante.", "estrategia")

    technical_terms = ["python", "script", "api", "sql", "streamlit", "bug", "backend", "frontend", "deploy", "docker"]
    if any(k in text for k in technical_terms):
        add("Codex", 3, "Hay señales claras de trabajo técnico o de programación.", "señales_técnicas")

    compare_terms = ["comparar", "alternativas", "opciones", "ideas", "brainstorm", "hipótesis", "hipotesis"]
    if any(k in text for k in compare_terms):
        add("ChatGPT", 2, "Conviene explorar opciones con rapidez.", "opciones")
        add("Gemini", 1, "Puede servir como segunda opinión.", "segunda_opinión")

    ranking = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    recommended = ranking[0][0]
    gap = ranking[0][1] - ranking[1][1]
    fit = "alto" if gap >= 3 else "medio" if gap >= 1 else "ajustado"

    primary_signals = sorted(
        [s for s in signals if s["model"] == recommended],
        key=lambda s: s["points"],
        reverse=True,
    )[:4]

    alternatives = []
    for model, _ in ranking[1:4]:
        notes = [s["reason"] for s in signals if s["model"] == model][:2]
        if not notes:
            notes = ["Puede servir como alternativa, pero no es la primera opción con las señales actuales."]
        alternatives.append({"model": model, "notes": notes})

    return {
        "recommended_model": recommended,
        "fit": fit,
        "scores": scores,
        "primary_signals": primary_signals,
        "alternatives": alternatives,
    }


def router_summary_from_data(data: Dict) -> str:
    lines = [
        f"Modelo recomendado: {data['recommended_model']}",
        f"Nivel de ajuste: {data['fit']}",
        "",
        "Motivos principales:",
    ]
    for signal in data["primary_signals"]:
        lines.append(f"- {signal['reason']}")
    lines.append("")
    lines.append("Puntuación comparada:")
    for model, score in sorted(data["scores"].items(), key=lambda x: x[1], reverse=True):
        lines.append(f"- {model}: {score}")
    return "\n".join(lines)


def build_prompt_blocks(project: sqlite3.Row, subproject: Optional[sqlite3.Row], task: Dict, suggested_model: str, inherited_docs: List[sqlite3.Row], task_uploads: List[Dict]) -> Dict:
    docs_project = "No hay documentos heredados."
    if inherited_docs:
        docs_project = "\n".join([f"- {d['title']} ({human_size(d['size_bytes'])})" for d in inherited_docs[:10]])

    docs_task = "No hay documentos adjuntos en la tarea."
    if task_uploads:
        docs_task = "\n".join([f"- {d['name']} ({human_size(d['size'])})" for d in task_uploads])

    inherited_context = effective_project_context(project, subproject)
    inherited_instructions = effective_project_instructions(project, subproject)

    system_prompt = f"""Actúa como un colaborador experto y riguroso.
Idioma de respuesta: castellano.
Prioriza claridad, criterio, estructura y utilidad práctica.
Respeta el contexto heredado del proyecto.

Contexto heredado:
{inherited_context or 'Sin contexto heredado definido.'}

Reglas estables heredadas:
{inherited_instructions or 'Sin reglas estables definidas.'}
"""

    subproject_line = f"\nSUBPROYECTO\n{subproject['name']}\n" if subproject else ""
    main_prompt = f"""PROYECTO
{project['name']}{subproject_line}
TAREA
{task['title']}

TIPO DE TRABAJO
{task['task_type']}

MODELO RECOMENDADO
{suggested_model}

OBJETIVO
{task['description']}

INSTRUCCIÓN
Ayúdame con esta tarea de forma clara, estructurada y accionable.

FORMATO DE RESPUESTA ESPERADO
1. Diagnóstico breve
2. Propuesta principal
3. Riesgos o límites
4. Siguiente paso concreto
"""

    return {
        "main_prompt": main_prompt,
        "inherited_context": inherited_context or "Sin contexto heredado definido.",
        "task_context": task["context"] or "Sin contexto específico de la tarea.",
        "inherited_documents": docs_project,
        "task_documents": docs_task,
        "system_prompt": system_prompt,
    }


def export_full_prompt(blocks: Dict) -> str:
    return f"""{blocks['main_prompt']}

CONTEXTO HEREDADO
{blocks['inherited_context']}

CONTEXTO DE LA TAREA
{blocks['task_context']}

DOCUMENTOS HEREDADOS
{blocks['inherited_documents']}

DOCUMENTOS DE LA TAREA
{blocks['task_documents']}

INSTRUCCIONES DEL SISTEMA
{blocks['system_prompt']}
"""


def create_task(project_id: int, subproject_id: Optional[int], title: str, description: str, task_type: str, tags: str, context: str, uploaded_files) -> int:
    created_at = now_iso()
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO tasks (
                project_id, subproject_id, title, description, task_type, status, tags, context,
                uploads_json, suggested_model, router_summary, router_data_json,
                prompt_main, prompt_system, llm_output, useful_extract,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, 'borrador', ?, ?, '[]', '', '', '', '', '', '', '', ?, ?)
            """,
            (
                project_id, subproject_id, title.strip(), description.strip(),
                task_type, tags.strip(), context.strip(), created_at, created_at,
            ),
        )
        task_id = int(cur.lastrowid)

        project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        subproject = conn.execute("SELECT * FROM subprojects WHERE id = ?", (subproject_id,)).fetchone() if subproject_id else None
        project_docs = conn.execute("SELECT * FROM project_documents WHERE project_id = ?", (project_id,)).fetchall()
        inherited_docs = effective_project_documents(project_docs, subproject)
        task_uploads = save_task_files(project_id, task_id, uploaded_files)

        inherited_context = effective_project_context(project, subproject)
        router = score_model(task_type, title, description, context, inherited_context, inherited_docs, task_uploads)
        router_summary = router_summary_from_data(router)
        task_payload = {"title": title, "description": description, "task_type": task_type, "context": context}
        prompt_blocks = build_prompt_blocks(project, subproject, task_payload, router["recommended_model"], inherited_docs, task_uploads)

        conn.execute(
            """
            UPDATE tasks
            SET uploads_json = ?, suggested_model = ?, router_summary = ?, router_data_json = ?,
                prompt_main = ?, prompt_system = ?, status = 'router_listo', updated_at = ?
            WHERE id = ?
            """,
            (
                json.dumps(task_uploads, ensure_ascii=False),
                router["recommended_model"],
                router_summary,
                json.dumps(router, ensure_ascii=False),
                prompt_blocks["main_prompt"],
                prompt_blocks["system_prompt"],
                now_iso(),
                task_id,
            ),
        )

        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        md_path = write_task_markdown(project, subproject, row)
        conn.execute("UPDATE tasks SET markdown_path = ?, updated_at = ? WHERE id = ?", (md_path, now_iso(), task_id))
    return task_id


def update_task(
    task_id: int,
    project: sqlite3.Row,
    subproject: Optional[sqlite3.Row],
    title: str,
    description: str,
    task_type: str,
    status: str,
    tags: str,
    context: str,
    uploads_json: str,
    suggested_model: str,
    router_summary: str,
    router_data_json: str,
    prompt_main: str,
    prompt_system: str,
    llm_output: str,
    useful_extract: str,
    subproject_id: Optional[int],
) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE tasks
            SET subproject_id = ?, title = ?, description = ?, task_type = ?, status = ?, tags = ?, context = ?,
                uploads_json = ?, suggested_model = ?, router_summary = ?, router_data_json = ?,
                prompt_main = ?, prompt_system = ?, llm_output = ?, useful_extract = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                subproject_id, title.strip(), description.strip(), task_type, status, tags.strip(), context.strip(),
                uploads_json, suggested_model, router_summary, router_data_json,
                prompt_main, prompt_system, llm_output, useful_extract, now_iso(), task_id,
            ),
        )
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        md_path = write_task_markdown(project, subproject, row)
        conn.execute("UPDATE tasks SET markdown_path = ?, updated_at = ? WHERE id = ?", (md_path, now_iso(), task_id))


def get_project_tasks(project_id: int, search: str = "", status_filter: str = "", subproject_filter: str = "") -> List[sqlite3.Row]:
    query = "SELECT * FROM tasks WHERE project_id = ?"
    params = [project_id]
    if search.strip():
        query += " AND (title LIKE ? OR description LIKE ? OR tags LIKE ? OR context LIKE ?)"
        pattern = f"%{search.strip()}%"
        params += [pattern, pattern, pattern, pattern]
    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)
    if subproject_filter:
        if subproject_filter == "__none__":
            query += " AND subproject_id IS NULL"
        else:
            query += " AND subproject_id = ?"
            params.append(int(subproject_filter))
    query += " ORDER BY updated_at DESC, id DESC"
    with get_conn() as conn:
        return conn.execute(query, params).fetchall()


def get_task(task_id: int) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()


def create_asset(project_id: int, subproject_id: Optional[int], task_id: int, title: str, summary: str, content: str) -> int:
    created_at = now_iso()
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO assets (project_id, subproject_id, task_id, title, summary, content, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (project_id, subproject_id, task_id, title.strip(), summary.strip(), content.strip(), created_at),
        )
        asset_id = int(cur.lastrowid)
        row = conn.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
        md_path = write_asset_markdown(row)
        conn.execute("UPDATE assets SET markdown_path = ? WHERE id = ?", (md_path, asset_id))
    return asset_id


def get_project_assets(project_id: int) -> List[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT a.*, t.title AS task_title
            FROM assets a
            JOIN tasks t ON a.task_id = t.id
            WHERE a.project_id = ?
            ORDER BY a.created_at DESC, a.id DESC
            """,
            (project_id,),
        ).fetchall()


def write_task_markdown(project: sqlite3.Row, subproject: Optional[sqlite3.Row], task: sqlite3.Row | dict) -> str:
    path = task_markdown_path(int(task["id"]), str(task["title"]))
    subproject_name = subproject["name"] if subproject else "Sin subproyecto"
    content = f"""# {task["title"]}

- Proyecto: {project["name"]}
- Subproyecto: {subproject_name}
- ID tarea: {task["id"]}
- Tipo: {task["task_type"]}
- Estado: {task["status"]}
- Modelo recomendado: {task["suggested_model"]}
- Etiquetas: {task["tags"]}
- Creado: {task["created_at"]}
- Actualizado: {task["updated_at"]}

## Contexto heredado
{effective_project_context(project, subproject)}

## Contexto específico de la tarea
{task["context"]}

## Resumen del router
{task["router_summary"]}

## Prompt principal
{task["prompt_main"]}

## Instrucciones del sistema
{task["prompt_system"]}

## Resultado del modelo
{task["llm_output"]}

## Extracto reusable
{task["useful_extract"]}
"""
    path.write_text(content, encoding="utf-8")
    return str(path)


def write_asset_markdown(asset: sqlite3.Row | dict) -> str:
    path = asset_markdown_path(int(asset["id"]), str(asset["title"]))
    content = f"""# {asset["title"]}

- ID activo: {asset["id"]}
- ID tarea: {asset["task_id"]}
- Creado: {asset["created_at"]}

## Resumen
{asset["summary"]}

## Contenido
{asset["content"]}
"""
    path.write_text(content, encoding="utf-8")
    return str(path)


def infer_step(task: sqlite3.Row) -> str:
    if task["useful_extract"]:
        return "Activo"
    if task["llm_output"]:
        return "Resultado"
    if task["prompt_main"]:
        return "Prompt"
    if task["router_summary"]:
        return "Router"
    return "Tarea"


def inject_css() -> None:
    st.markdown(
        """
        <style>
        .stApp { background: #F7F9FC; color: #0F172A; }
        .block-container { max-width: 1480px; padding-top: 1rem; padding-bottom: 1.6rem; padding-left: 1.4rem; padding-right: 1.4rem; }
        h1, h2, h3 { color: #0F172A; letter-spacing: -0.02em; }
        [data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid #E2E8F0; }
        [data-testid="stSidebar"] * { color: #0F172A !important; }
        .panel, .card { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 18px; padding: 1rem 1.1rem; box-shadow: 0 1px 2px rgba(15,23,42,0.04); }
        .card { margin-bottom: 0.9rem; }
        .muted { color: #475569; font-size: 0.92rem; }
        .meta { color: #94A3B8; font-size: 0.82rem; }
        .metric { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; padding: 0.85rem 0.95rem; }
        .pill { display: inline-block; padding: 0.16rem 0.5rem; border-radius: 999px; border: 1px solid #E2E8F0; color: #475569; background: #FFFFFF; font-size: 0.76rem; margin-right: 0.35rem; }
        .project-row, .task-row, .subproject-row { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; padding: 0.9rem 0.95rem; margin-bottom: 0.75rem; }
        .task-row.selected { border: 2px solid #1E293B; }
        .stepper { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1rem; }
        .step { padding: 0.5rem 0.75rem; border-radius: 999px; border: 1px solid #E2E8F0; background: #FFFFFF; color: #475569; font-size: 0.84rem; font-weight: 600; }
        .step.active { background: #1E293B; color: #FFFFFF; border-color: #1E293B; }
        .step.done { background: #F8FAFC; color: #475569; border-color: #E2E8F0; }
        .router-box { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 18px; padding: 1rem 1.1rem; }
        .router-model { font-size: 1.9rem; font-weight: 800; color: #0F172A; margin-top: 0.1rem; }
        div[data-baseweb="select"] > div, .stTextInput input, .stTextArea textarea { border-radius: 12px !important; border: 1px solid #E2E8F0 !important; background: #FFFFFF !important; color: #0F172A !important; }
        div.stButton > button, .stDownloadButton > button, div[data-testid="stFormSubmitButton"] > button { border-radius: 12px !important; border: 1px solid #CBD5E1 !important; background: #FFFFFF !important; color: #0F172A !important; padding: 0.55rem 0.9rem !important; font-weight: 600 !important; }
        div.stButton > button:hover, .stDownloadButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover { border-color: #94A3B8 !important; background: #F8FAFC !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_topbar() -> None:
    projects = get_projects()
    total_tasks = sum([p["task_count"] for p in projects])
    total_assets = sum([p["asset_count"] for p in projects])

    c1, c2 = st.columns([2.2, 1.4])
    with c1:
        st.markdown(
            """
            <div class="card">
                <h1 style="margin:0;">Portable Work Router</h1>
                <div class="muted">Trabajo por proyecto y subproyecto, con herencia de contexto y router contextual.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        m1, m2, m3 = st.columns(3)
        m1.markdown(f'<div class="metric"><div class="meta">Proyectos</div><div style="font-size:1.4rem;font-weight:700;">{len(projects)}</div></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="metric"><div class="meta">Tareas</div><div style="font-size:1.4rem;font-weight:700;">{total_tasks}</div></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="metric"><div class="meta">Activos</div><div style="font-size:1.4rem;font-weight:700;">{total_assets}</div></div>', unsafe_allow_html=True)


def render_stepper(current_step: str) -> None:
    current_idx = PASOS.index(current_step)
    parts = []
    for i, step in enumerate(PASOS):
        cls = "step"
        if i < current_idx:
            cls += " done"
        elif i == current_idx:
            cls += " active"
        parts.append(f'<div class="{cls}">{i+1}. {step}</div>')
    st.markdown('<div class="stepper">' + "".join(parts) + '</div>', unsafe_allow_html=True)


def view_projects() -> None:
    st.subheader("Proyectos")
    left, right = st.columns([1.35, 1], gap="large")

    with left:
        projects = get_projects()
        if not projects:
            st.markdown('<div class="card">Todavía no hay proyectos creados.</div>', unsafe_allow_html=True)
        for p in projects:
            st.markdown(
                f"""
                <div class="project-row">
                    <div style="font-weight:700; font-size:1.02rem;">{p["name"]}</div>
                    <div class="muted" style="margin:0.2rem 0 0.45rem 0;">{p["description"] or "Sin descripción."}</div>
                    <span class="pill">{p["task_count"]} tareas</span>
                    <span class="pill">{p["subproject_count"]} subproyectos</span>
                    <span class="pill">{p["asset_count"]} activos</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(f"Abrir proyecto #{p['id']}", key=f"open_project_{p['id']}", use_container_width=True):
                st.session_state["selected_project_id"] = int(p["id"])
                st.rerun()

    with right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("### Crear proyecto")
        name = st.text_input("Nombre del proyecto", placeholder="Ej.: Portable Work Router", help="Cómo quieres identificar este espacio de trabajo.")
        description = st.text_area("Descripción breve", placeholder="Qué es este proyecto.", height=90, help="Resumen corto para reconocer rápidamente de qué trata el proyecto.")
        objective = st.text_area("Objetivo del proyecto", placeholder="Para qué existe el proyecto.", height=90, help="Qué intenta conseguir este proyecto.")
        base_context = st.text_area("Contexto de referencia del proyecto", placeholder="Contexto estable del proyecto.", height=140, help="Antecedentes, decisiones previas, restricciones o información que no quieres repetir en cada tarea.")
        base_instructions = st.text_area("Reglas estables del proyecto", placeholder="Reglas, estilo, restricciones o convenciones.", height=120, help="Idioma, tono, formato o criterios que deberían aplicarse siempre en este proyecto.")
        tags = st.text_input("Etiquetas", placeholder="pwr, producto, b2b", help="Palabras clave para organizar y localizar mejor el proyecto.")
        project_files = st.file_uploader("Documentos de referencia del proyecto", accept_multiple_files=True, key="project_files", help="Archivos que forman parte del contexto general del proyecto, no de una tarea puntual.")

        if project_files:
            st.markdown("**Documentos seleccionados**")
            for f in project_files:
                st.markdown(f"- {f.name} ({human_size(f.size)})")

        if st.button("Dar de alta el proyecto", use_container_width=True):
            if not name.strip():
                st.error("El nombre del proyecto es obligatorio.")
            else:
                project_id = create_project(name, description, objective, base_context, base_instructions, tags, project_files)
                st.session_state["selected_project_id"] = project_id
                st.success("Proyecto creado.")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


def view_project_workspace() -> None:
    project_id = st.session_state.get("selected_project_id")
    if not project_id:
        st.info("Selecciona primero un proyecto en la pestaña Proyectos.")
        return

    project = get_project(int(project_id))
    if not project:
        st.warning("No se pudo cargar el proyecto.")
        return

    docs = get_project_documents(project["id"])
    subprojects = get_subprojects(project["id"])
    tasks = get_project_tasks(project["id"])
    assets = get_project_assets(project["id"])

    tags = ", ".join(safe_json_loads(project["tags_json"], []))
    st.markdown(
        f"""
        <div class="card">
            <div style="display:flex;justify-content:space-between;gap:1rem;align-items:flex-start;flex-wrap:wrap;">
                <div>
                    <div style="font-size:1.4rem;font-weight:700;">{project["name"]}</div>
                    <div class="muted" style="margin-top:0.2rem;">{project["description"] or "Sin descripción."}</div>
                    <div style="margin-top:0.55rem;">
                        <span class="pill">{len(tasks)} tareas</span>
                        <span class="pill">{len(subprojects)} subproyectos</span>
                        <span class="pill">{len(assets)} activos</span>
                        <span class="pill">{len(docs)} documentos</span>
                    </div>
                </div>
                <div>
                    <span class="pill">{project["status"]}</span>
                    {f'<span class="pill">{tags}</span>' if tags else ''}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    expand_key = f"project_info_expanded_{project['id']}"
    edit_key = f"project_edit_mode_{project['id']}"

    if expand_key not in st.session_state:
        st.session_state[expand_key] = False
    if edit_key not in st.session_state:
        st.session_state[edit_key] = False

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    h1, h2, h3 = st.columns([1.2, 1, 1])
    with h1:
        st.markdown("### Información del proyecto")
    with h2:
        if st.button(
            "Ocultar información" if st.session_state[expand_key] else "Mostrar información",
            use_container_width=True,
            key=f"btn_toggle_project_{project['id']}",
        ):
            st.session_state[expand_key] = not st.session_state[expand_key]
            if not st.session_state[expand_key]:
                st.session_state[edit_key] = False
            st.rerun()
    with h3:
        if st.session_state[expand_key]:
            st.session_state[edit_key] = st.toggle(
                "Modo edición",
                value=st.session_state[edit_key],
                key=f"toggle_edit_project_{project['id']}",
            )

    if st.session_state[expand_key]:
        if not st.session_state[edit_key]:
            st.markdown("**Objetivo del proyecto**")
            st.write(project["objective"] or "Sin objetivo definido.")
            st.markdown("**Contexto de referencia del proyecto**")
            st.write(project["base_context"] or "Sin contexto base definido.")
            st.markdown("**Reglas estables del proyecto**")
            st.write(project["base_instructions"] or "Sin reglas estables definidas.")
            tags_list = safe_json_loads(project["tags_json"], [])
            if tags_list:
                st.markdown("**Etiquetas**")
                st.write(", ".join(tags_list))
        else:
            name = st.text_input("Nombre del proyecto", value=project["name"], key=f"edit_name_{project['id']}")
            description = st.text_area("Descripción breve", value=project["description"], height=90, key=f"edit_desc_{project['id']}")
            objective = st.text_area("Objetivo del proyecto", value=project["objective"], height=90, key=f"edit_obj_{project['id']}")
            base_context = st.text_area("Contexto de referencia del proyecto", value=project["base_context"], height=160, key=f"edit_ctx_{project['id']}")
            base_instructions = st.text_area("Reglas estables del proyecto", value=project["base_instructions"], height=140, key=f"edit_instr_{project['id']}")
            tags_value = ", ".join(safe_json_loads(project["tags_json"], []))
            tags = st.text_input("Etiquetas", value=tags_value, key=f"edit_tags_{project['id']}")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Guardar cambios del proyecto", use_container_width=True, key=f"save_project_{project['id']}"):
                    update_project(project["id"], name, description, objective, base_context, base_instructions, tags)
                    st.session_state[edit_key] = False
                    st.success("Proyecto actualizado.")
                    st.rerun()
            with c2:
                if st.button("Cancelar edición", use_container_width=True, key=f"cancel_project_{project['id']}"):
                    st.session_state[edit_key] = False
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    tab_resumen, tab_subproyectos, tab_tareas, tab_activos, tab_documentos = st.tabs(
        ["Resumen", "Subproyectos", "Tareas", "Activos", "Documentos"]
    )

    with tab_resumen:
        c1, c2 = st.columns([1.25, 1], gap="large")
        with c1:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown("### Contexto efectivo del proyecto")
            st.write(project["base_context"] or "Sin contexto base definido.")
            st.markdown("### Reglas estables")
            st.write(project["base_instructions"] or "Sin reglas estables definidas.")
            st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown("### Actividad reciente")
            if tasks:
                for t in tasks[:6]:
                    sub = get_subproject(t["subproject_id"])
                    suffix = f" · {sub['name']}" if sub else ""
                    st.markdown(f"- **{t['title']}**{suffix} · {t['status']}")
            else:
                st.write("Todavía no hay tareas.")
            st.markdown('</div>', unsafe_allow_html=True)

    with tab_subproyectos:
        render_subprojects_tab(project, subprojects)

    with tab_tareas:
        render_tasks_tab(project, docs, subprojects)

    with tab_activos:
        if not assets:
            st.markdown('<div class="card">Todavía no hay activos creados en este proyecto.</div>', unsafe_allow_html=True)
        for a in assets:
            sub = get_subproject(a["subproject_id"])
            sub_label = f" · {sub['name']}" if sub else ""
            st.markdown(
                f"""
                <div class="card">
                    <div style="font-weight:700;">{a["title"]}</div>
                    <div class="muted" style="margin:0.2rem 0 0.45rem 0;">Procede de: {a["task_title"]}{sub_label}</div>
                    <div><strong>Resumen</strong><br>{a["summary"] or "Sin resumen."}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if a["markdown_path"] and Path(a["markdown_path"]).exists():
                content = Path(a["markdown_path"]).read_text(encoding="utf-8")
                st.download_button(
                    f"Descargar activo #{a['id']}",
                    data=content,
                    file_name=Path(a["markdown_path"]).name,
                    mime="text/markdown",
                    key=f"asset_{a['id']}",
                    use_container_width=True,
                )

    with tab_documentos:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("### Documentos del proyecto")
        if not docs:
            st.write("No hay documentos asociados a este proyecto.")
        else:
            for d in docs:
                st.markdown(f"- **{d['title']}** · {human_size(d['size_bytes'])} · {d['document_role']}")
        st.markdown('</div>', unsafe_allow_html=True)


def render_subprojects_tab(project: sqlite3.Row, subprojects: List[sqlite3.Row]) -> None:
    left, right = st.columns([1.15, 1], gap="large")
    with left:
        if not subprojects:
            st.markdown('<div class="card">Todavía no hay subproyectos.</div>', unsafe_allow_html=True)
        for s in subprojects:
            tags = ", ".join(safe_json_loads(s["tags_json"], []))
            st.markdown(
                f"""
                <div class="subproject-row">
                    <div style="font-weight:700;">{s["name"]}</div>
                    <div class="muted" style="margin:0.2rem 0 0.45rem 0;">{s["description"] or "Sin descripción."}</div>
                    <span class="pill">{s["task_count"]} tareas</span>
                    <span class="pill">{s["asset_count"]} activos</span>
                    <span class="pill">{'hereda contexto' if s["inherit_project_context"] else 'sin herencia de contexto'}</span>
                    {f'<span class="pill">{tags}</span>' if tags else ''}
                </div>
                """,
                unsafe_allow_html=True,
            )
    with right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("### Crear subproyecto")
        name = st.text_input("Nombre del subproyecto", placeholder="Ej.: Router de modelos", help="Línea de trabajo dentro del proyecto.")
        description = st.text_area("Descripción", placeholder="Qué aborda este subproyecto.", height=80)
        objective = st.text_area("Objetivo", placeholder="Qué pretende resolver este subproyecto.", height=80)
        inherit_context = st.checkbox("Heredar contexto del proyecto", value=True)
        inherit_documents = st.checkbox("Heredar documentos del proyecto", value=True)
        local_context = st.text_area("Contexto específico del subproyecto", placeholder="Información adicional que solo aplica aquí.", height=120)
        local_instructions = st.text_area("Reglas del subproyecto", placeholder="Opcional. Sobrescribe parcialmente las del proyecto.", height=100)
        tags = st.text_input("Etiquetas", placeholder="router, benchmark, modelos")
        if st.button("Crear subproyecto", use_container_width=True):
            if not name.strip():
                st.error("El nombre del subproyecto es obligatorio.")
            else:
                create_subproject(project["id"], name, description, objective, inherit_context, inherit_documents, local_context, local_instructions, tags)
                st.success("Subproyecto creado.")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


def render_tasks_tab(project: sqlite3.Row, project_docs: List[sqlite3.Row], subprojects: List[sqlite3.Row]) -> None:
    tasks = get_project_tasks(project["id"])
    selected_task_id = st.session_state.get("selected_task_id")
    if tasks and selected_task_id not in [int(t["id"]) for t in tasks]:
        selected_task_id = int(tasks[0]["id"])
        st.session_state["selected_task_id"] = selected_task_id

    left, right = st.columns([0.98, 2.02], gap="large")

    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("### Nueva tarea")
        title = st.text_input("Título", placeholder="Ej.: Revisar el router del proyecto")
        task_type = st.selectbox("Tipo de trabajo", list(TIPOS_TAREA.keys()))
        subproject_options = [("__none__", "Sin subproyecto")] + [(str(s["id"]), s["name"]) for s in subprojects]
        chosen_sub = st.selectbox("Subproyecto", options=[opt[0] for opt in subproject_options], format_func=lambda x: dict(subproject_options)[x])
        tags = st.text_input("Etiquetas", placeholder="router, ux, prioridad")
        description = st.text_area("Descripción", placeholder="Qué necesitas conseguir.", height=100)
        context = st.text_area("Contexto específico", placeholder="Notas concretas de esta tarea.", height=130)
        task_files = st.file_uploader("Documentos de la tarea", accept_multiple_files=True, key="task_files", help="Adjuntos específicos de esta tarea.")
        if task_files:
            for f in task_files:
                st.markdown(f"- {f.name} ({human_size(f.size)})")
        if st.button("Crear tarea", use_container_width=True):
            if not title.strip() or not description.strip():
                st.error("Título y descripción son obligatorios.")
            else:
                subproject_id = None if chosen_sub == "__none__" else int(chosen_sub)
                task_id = create_task(project["id"], subproject_id, title, description, task_type, tags, context, task_files)
                st.session_state["selected_task_id"] = task_id
                st.session_state[f"step_{task_id}"] = "Router"
                st.success("Tarea creada.")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.write("")

        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("### Tareas del proyecto")
        search = st.text_input("Buscar en tus tareas", placeholder="Título, contenido o etiqueta", key=f"search_{project['id']}")
        status_filter = st.selectbox("Estado", ["", *ESTADOS_TAREA], index=0, format_func=lambda x: "Todos" if x == "" else x, key=f"status_{project['id']}")
        sub_filter_options = [("", "Todos"), ("__none__", "Sin subproyecto")] + [(str(s["id"]), s["name"]) for s in subprojects]
        sub_filter = st.selectbox("Filtrar por subproyecto", options=[x[0] for x in sub_filter_options], format_func=lambda x: dict(sub_filter_options)[x], key=f"subfilter_{project['id']}")
        filtered = get_project_tasks(project["id"], search=search, status_filter=status_filter, subproject_filter=sub_filter)
        if not filtered:
            st.write("No hay tareas con ese criterio.")
        for t in filtered:
            selected_class = " selected" if int(t["id"]) == selected_task_id else ""
            sub = get_subproject(t["subproject_id"])
            sub_label = sub["name"] if sub else "Sin subproyecto"
            st.markdown(
                f"""
                <div class="task-row{selected_class}">
                    <div style="font-weight:700;">{t["title"]}</div>
                    <div class="muted" style="margin:0.2rem 0 0.45rem 0;">{t["description"][:90]}{"..." if len(t["description"]) > 90 else ""}</div>
                    <span class="pill">{t["task_type"]}</span>
                    <span class="pill">{sub_label}</span>
                    <span class="pill">{infer_step(t)}</span>
                    <span class="pill">{t["suggested_model"] or "Sin router"}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(f"Abrir #{t['id']}", key=f"open_task_{t['id']}", use_container_width=True):
                st.session_state["selected_task_id"] = int(t["id"])
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        if not selected_task_id:
            st.markdown('<div class="card">Selecciona o crea una tarea para trabajar.</div>', unsafe_allow_html=True)
            return

        task = get_task(int(selected_task_id))
        if not task:
            st.warning("No se pudo cargar la tarea.")
            return

        subproject = get_subproject(task["subproject_id"])
        task_uploads = safe_json_loads(task["uploads_json"], [])
        current_step = st.session_state.get(f"step_{task['id']}", infer_step(task))
        st.session_state[f"step_{task['id']}"] = current_step

        inherited_context = effective_project_context(project, subproject)
        inherited_instructions = effective_project_instructions(project, subproject)
        inherited_docs = effective_project_documents(project_docs, subproject)

        router_data = safe_json_loads(task["router_data_json"], {})
        if not router_data:
            router_data = score_model(task["task_type"], task["title"], task["description"], task["context"], inherited_context, inherited_docs, task_uploads)

        prompt_blocks = build_prompt_blocks(
            project, subproject,
            {"title": task["title"], "description": task["description"], "task_type": task["task_type"], "context": task["context"]},
            task["suggested_model"] or router_data["recommended_model"],
            inherited_docs,
            task_uploads,
        )
        full_prompt = export_full_prompt(prompt_blocks)

        sub_label = f" · {subproject['name']}" if subproject else ""
        st.markdown(
            f"""
            <div class="card">
                <div style="font-size:1.15rem;font-weight:700;">{task["title"]}</div>
                <div class="muted">{task["description"]}</div>
                <div style="margin-top:0.5rem;">
                    <span class="pill">{project["name"]}</span>
                    <span class="pill">{subproject['name'] if subproject else 'Sin subproyecto'}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_stepper(current_step)

        if current_step == "Tarea":
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            title = st.text_input("Título de la tarea", value=task["title"], key=f"title_{task['id']}")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                task_type = st.selectbox("Tipo de trabajo", list(TIPOS_TAREA.keys()), index=list(TIPOS_TAREA.keys()).index(task["task_type"]), key=f"type_{task['id']}")
            with c2:
                status = st.selectbox("Estado", ESTADOS_TAREA, index=ESTADOS_TAREA.index(task["status"]) if task["status"] in ESTADOS_TAREA else 0, key=f"status_task_{task['id']}")
            with c3:
                tags = st.text_input("Etiquetas", value=task["tags"], key=f"tags_{task['id']}")
            with c4:
                current_sub_opts = [("__none__", "Sin subproyecto")] + [(str(s["id"]), s["name"]) for s in subprojects]
                current_sub_val = "__none__" if task["subproject_id"] is None else str(task["subproject_id"])
                chosen_sub = st.selectbox("Subproyecto", options=[x[0] for x in current_sub_opts], index=[x[0] for x in current_sub_opts].index(current_sub_val), format_func=lambda x: dict(current_sub_opts)[x], key=f"subchoice_{task['id']}")
            description = st.text_area("Descripción", value=task["description"], height=100, key=f"desc_{task['id']}")
            context = st.text_area("Contexto específico", value=task["context"], height=220, key=f"ctx_{task['id']}")
            st.markdown("**Contexto heredado efectivo**")
            st.write(inherited_context or "Sin contexto heredado.")
            if task_uploads:
                st.markdown("**Documentos asociados a la tarea**")
                for d in task_uploads:
                    st.markdown(f"- {d['name']} ({human_size(d['size'])})")
            b1, b2 = st.columns(2)
            with b1:
                if st.button("Guardar tarea", use_container_width=True, key=f"save_task_{task['id']}"):
                    new_subproject_id = None if chosen_sub == "__none__" else int(chosen_sub)
                    new_subproject = get_subproject(new_subproject_id)
                    new_inherited_context = effective_project_context(project, new_subproject)
                    new_inherited_docs = effective_project_documents(project_docs, new_subproject)
                    new_router = score_model(task_type, title, description, context, new_inherited_context, new_inherited_docs, task_uploads)
                    new_summary = router_summary_from_data(new_router)
                    new_blocks = build_prompt_blocks(
                        project, new_subproject,
                        {"title": title, "description": description, "task_type": task_type, "context": context},
                        new_router["recommended_model"], new_inherited_docs, task_uploads,
                    )
                    update_task(
                        int(task["id"]), project, new_subproject, title, description, task_type, status, tags, context,
                        task["uploads_json"], new_router["recommended_model"], new_summary,
                        json.dumps(new_router, ensure_ascii=False), new_blocks["main_prompt"],
                        new_blocks["system_prompt"], task["llm_output"], task["useful_extract"], new_subproject_id
                    )
                    st.success("Tarea guardada.")
                    st.rerun()
            with b2:
                if st.button("Siguiente: router", use_container_width=True, key=f"next_router_{task['id']}"):
                    st.session_state[f"step_{task['id']}"] = "Router"
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        elif current_step == "Router":
            st.markdown(
                f"""
                <div class="router-box">
                    <div class="meta">Recomendación de modelo</div>
                    <div class="router-model">{router_data['recommended_model']}</div>
                    <div class="muted" style="margin-top:0.25rem;">Nivel de ajuste: {router_data['fit']}</div>
                    <div class="muted" style="margin-top:0.4rem;">Proyecto: {project['name']} · {subproject['name'] if subproject else 'Sin subproyecto'}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.write("")
            c1, c2 = st.columns([1.25, 1], gap="large")
            with c1:
                st.markdown("### Justificación técnica")
                reasons = "\n".join([f"- **{s['metric'].replace('_', ' ').capitalize()}**: {s['reason']}" for s in router_data["primary_signals"]]) or "- Sin señales detectadas."
                st.markdown(reasons)
                st.markdown("### Puntuación comparada")
                st.markdown("\n".join([f"- **{m}**: {s}" for m, s in sorted(router_data["scores"].items(), key=lambda x: x[1], reverse=True)]))
            with c2:
                st.markdown("### Herencia de contexto")
                st.markdown(f"**Contexto heredado:** {'sí' if inherited_context else 'no'}")
                st.markdown(f"**Documentos heredados:** {len(inherited_docs)}")
                st.markdown("### Alternativas")
                for alt in router_data["alternatives"]:
                    st.markdown(f"**{alt['model']}**")
                    for note in alt["notes"]:
                        st.markdown(f"- {note}")

            b1, b2, b3 = st.columns(3)
            with b1:
                if st.button("Volver a tarea", use_container_width=True, key=f"back_task_{task['id']}"):
                    st.session_state[f"step_{task['id']}"] = "Tarea"
                    st.rerun()
            with b2:
                if st.button("Recalcular router", use_container_width=True, key=f"recalc_{task['id']}"):
                    new_router = score_model(task["task_type"], task["title"], task["description"], task["context"], inherited_context, inherited_docs, task_uploads)
                    new_summary = router_summary_from_data(new_router)
                    new_blocks = build_prompt_blocks(
                        project, subproject,
                        {"title": task["title"], "description": task["description"], "task_type": task["task_type"], "context": task["context"]},
                        new_router["recommended_model"], inherited_docs, task_uploads,
                    )
                    update_task(
                        int(task["id"]), project, subproject, task["title"], task["description"], task["task_type"], "router_listo", task["tags"], task["context"],
                        task["uploads_json"], new_router["recommended_model"], new_summary,
                        json.dumps(new_router, ensure_ascii=False), new_blocks["main_prompt"],
                        new_blocks["system_prompt"], task["llm_output"], task["useful_extract"], task["subproject_id"]
                    )
                    st.success("Router recalculado.")
                    st.rerun()
            with b3:
                if st.button("Aceptar y seguir al prompt", use_container_width=True, key=f"next_prompt_{task['id']}"):
                    st.session_state[f"step_{task['id']}"] = "Prompt"
                    st.rerun()

        elif current_step == "Prompt":
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown("### Prompt listo para usar")
            st.code(prompt_blocks["main_prompt"], language="markdown")
            b1, b2, b3 = st.columns(3)
            with b1:
                st.download_button("Exportar prompt", data=full_prompt, file_name=f"prompt-task-{task['id']}.md", mime="text/markdown", use_container_width=True)
            with b2:
                if st.button("Volver al router", use_container_width=True, key=f"back_router_{task['id']}"):
                    st.session_state[f"step_{task['id']}"] = "Router"
                    st.rerun()
            with b3:
                if st.button("Ya tengo el resultado", use_container_width=True, key=f"next_result_{task['id']}"):
                    st.session_state[f"step_{task['id']}"] = "Resultado"
                    st.rerun()

            with st.expander("Ver contexto heredado"):
                st.text_area("Contexto heredado", value=prompt_blocks["inherited_context"], height=180, disabled=True, label_visibility="collapsed")
            with st.expander("Ver contexto de la tarea"):
                st.text_area("Contexto de la tarea", value=prompt_blocks["task_context"], height=160, disabled=True, label_visibility="collapsed")
            with st.expander("Ver documentos heredados"):
                st.text_area("Documentos heredados", value=prompt_blocks["inherited_documents"], height=120, disabled=True, label_visibility="collapsed")
            with st.expander("Ver documentos de la tarea"):
                st.text_area("Documentos de la tarea", value=prompt_blocks["task_documents"], height=120, disabled=True, label_visibility="collapsed")
            with st.expander("Ver instrucciones del sistema"):
                st.text_area("Instrucciones del sistema", value=prompt_blocks["system_prompt"], height=180, disabled=True, label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)

        elif current_step == "Resultado":
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            llm_output = st.text_area("Resultado del modelo", value=task["llm_output"], height=280)
            useful_extract = st.text_area("Extracto reusable", value=task["useful_extract"], height=220)
            b1, b2, b3 = st.columns(3)
            with b1:
                if st.button("Volver al prompt", use_container_width=True, key=f"back_prompt_{task['id']}"):
                    st.session_state[f"step_{task['id']}"] = "Prompt"
                    st.rerun()
            with b2:
                if st.button("Guardar resultado", use_container_width=True, key=f"save_result_{task['id']}"):
                    update_task(
                        int(task["id"]), project, subproject, task["title"], task["description"], task["task_type"], "ejecutado", task["tags"], task["context"],
                        task["uploads_json"], task["suggested_model"], task["router_summary"], task["router_data_json"],
                        task["prompt_main"], task["prompt_system"], llm_output, useful_extract, task["subproject_id"]
                    )
                    st.success("Resultado guardado.")
                    st.rerun()
            with b3:
                if st.button("Siguiente: activo", use_container_width=True, key=f"next_asset_{task['id']}"):
                    update_task(
                        int(task["id"]), project, subproject, task["title"], task["description"], task["task_type"], "ejecutado", task["tags"], task["context"],
                        task["uploads_json"], task["suggested_model"], task["router_summary"], task["router_data_json"],
                        task["prompt_main"], task["prompt_system"], llm_output, useful_extract, task["subproject_id"]
                    )
                    st.session_state[f"step_{task['id']}"] = "Activo"
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        elif current_step == "Activo":
            default_content = task["useful_extract"].strip() or task["llm_output"].strip()
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            asset_title = st.text_input("Título del activo", value=f"Activo · {task['title']}")
            asset_summary = st.text_area("Resumen", value=task["description"], height=90)
            asset_content = st.text_area("Contenido final", value=default_content, height=260)
            b1, b2, b3 = st.columns(3)
            with b1:
                if st.button("Volver al resultado", use_container_width=True, key=f"back_result_{task['id']}"):
                    st.session_state[f"step_{task['id']}"] = "Resultado"
                    st.rerun()
            with b2:
                if st.button("Crear activo", use_container_width=True, key=f"create_asset_{task['id']}"):
                    if not asset_content.strip():
                        st.error("No hay contenido para convertir en activo.")
                    else:
                        create_asset(project["id"], task["subproject_id"], int(task["id"]), asset_title, asset_summary, asset_content)
                        st.success("Activo creado.")
                        st.rerun()
            with b3:
                if task["markdown_path"] and Path(task["markdown_path"]).exists():
                    content = Path(task["markdown_path"]).read_text(encoding="utf-8")
                    st.download_button("Descargar ficha de tarea", data=content, file_name=Path(task["markdown_path"]).name, mime="text/markdown", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    init_db()
    inject_css()

    with st.sidebar:
        st.markdown("## Portable Work Router")
        page = st.radio("Navegación", ["Proyectos", "Proyecto activo"], label_visibility="collapsed")
        st.caption("Castellano · B2B · proyecto → subproyecto → tarea")

    render_topbar()
    st.write("")

    if page == "Proyectos":
        view_projects()
    else:
        view_project_workspace()


if __name__ == "__main__":
    main()
