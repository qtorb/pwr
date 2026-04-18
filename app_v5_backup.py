
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
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
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
                FOREIGN KEY(project_id) REFERENCES projects(id)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                task_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                summary TEXT DEFAULT '',
                content TEXT NOT NULL,
                markdown_path TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id),
                FOREIGN KEY(task_id) REFERENCES tasks(id)
            )
            """
        )

        task_cols = [row["name"] for row in conn.execute("PRAGMA table_info(tasks)").fetchall()]
        if "project_id" not in task_cols:
            conn.execute("ALTER TABLE tasks ADD COLUMN project_id INTEGER")
        if "uploads_json" not in task_cols:
            conn.execute("ALTER TABLE tasks ADD COLUMN uploads_json TEXT DEFAULT '[]'")
        if "router_summary" not in task_cols:
            conn.execute("ALTER TABLE tasks ADD COLUMN router_summary TEXT DEFAULT ''")
        if "router_data_json" not in task_cols:
            conn.execute("ALTER TABLE tasks ADD COLUMN router_data_json TEXT DEFAULT ''")
        if "prompt_main" not in task_cols:
            conn.execute("ALTER TABLE tasks ADD COLUMN prompt_main TEXT DEFAULT ''")
        if "prompt_system" not in task_cols:
            conn.execute("ALTER TABLE tasks ADD COLUMN prompt_system TEXT DEFAULT ''")

        asset_cols = [row["name"] for row in conn.execute("PRAGMA table_info(assets)").fetchall()]
        if "project_id" not in asset_cols:
            conn.execute("ALTER TABLE assets ADD COLUMN project_id INTEGER")


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
                name.strip(),
                slug,
                description.strip(),
                objective.strip(),
                base_context.strip(),
                base_instructions.strip(),
                json.dumps([t.strip() for t in tags.split(",") if t.strip()], ensure_ascii=False),
                created_at,
                created_at,
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
                    project_id,
                    item["name"],
                    item["name"],
                    item["path"],
                    item["mime_type"],
                    item["size"],
                    created_at,
                    created_at,
                ),
            )
    return project_id


def get_projects() -> List[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT p.*,
                   (SELECT COUNT(*) FROM tasks t WHERE t.project_id = p.id AND t.status != 'archivado') AS task_count,
                   (SELECT COUNT(*) FROM assets a WHERE a.project_id = p.id) AS asset_count
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


def score_model(task_type: str, title: str, description: str, task_context: str, project_context: str, project_docs: List[sqlite3.Row], task_uploads: List[Dict]) -> Dict:
    text = f"{title} {description} {task_context} {project_context}".lower()
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
        add("Claude Sonnet", 3, "Ayuda a ordenar mejor una reflexión con más estructura.", "profundidad")
    elif task_type == "Programar":
        add("Codex", 7, "La tarea está orientada a código, debugging o implementación.", "código")
        add("ChatGPT", 1, "Puede apoyar como contraste rápido.", "apoyo")
    elif task_type == "Revisar":
        add("Claude Sonnet", 4, "La revisión se beneficia de lectura atenta y respuesta cuidada.", "revisión")
        add("ChatGPT", 2, "Puede servir como contraste y resumen rápido.", "contraste")
    elif task_type == "Decidir":
        add("ChatGPT", 4, "Conviene comparar opciones y avanzar con agilidad.", "decisión")
        add("Claude Sonnet", 2, "Puede ordenar mejor trade-offs complejos.", "trade_offs")

    total_context_len = len((task_context or "").strip()) + len((project_context or "").strip())
    if total_context_len > 400:
        add("Claude Sonnet", 2, "Hay bastante contexto acumulado y conviene priorizar profundidad.", "contexto")
    if total_context_len > 1000:
        add("Claude Sonnet", 2, "El volumen de contexto es alto y penaliza modelos menos sólidos en lectura larga.", "contexto_extenso")

    if project_docs:
        add("Claude Sonnet", 2, "El proyecto ya tiene documentación persistente asociada.", "documentación_proyecto")
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
    second = ranking[1][0]
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


def build_prompt_blocks(project: sqlite3.Row, task: Dict, suggested_model: str, project_docs: List[sqlite3.Row], task_uploads: List[Dict]) -> Dict:
    docs_project = "No hay documentos del proyecto."
    if project_docs:
        docs_project = "\n".join([f"- {d['title']} ({human_size(d['size_bytes'])})" for d in project_docs[:10]])

    docs_task = "No hay documentos adjuntos en la tarea."
    if task_uploads:
        docs_task = "\n".join([f"- {d['name']} ({human_size(d['size'])})" for d in task_uploads])

    system_prompt = f"""Actúa como un colaborador experto y riguroso.
Idioma de respuesta: castellano.
Prioriza claridad, criterio, estructura y utilidad práctica.
Respeta el contexto del proyecto y evita repetir información innecesaria.

Contexto estable del proyecto:
{project['base_context'] or 'Sin contexto base definido.'}

Instrucciones estables del proyecto:
{project['base_instructions'] or 'Sin instrucciones adicionales.'}
"""

    main_prompt = f"""PROYECTO
{project['name']}

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
        "project_context": project["base_context"] or "Sin contexto base definido.",
        "task_context": task["context"] or "Sin contexto específico de la tarea.",
        "project_documents": docs_project,
        "task_documents": docs_task,
        "system_prompt": system_prompt,
    }


def export_full_prompt(blocks: Dict) -> str:
    return f"""{blocks['main_prompt']}

CONTEXTO DEL PROYECTO
{blocks['project_context']}

CONTEXTO DE LA TAREA
{blocks['task_context']}

DOCUMENTOS DEL PROYECTO
{blocks['project_documents']}

DOCUMENTOS DE LA TAREA
{blocks['task_documents']}

INSTRUCCIONES DEL SISTEMA
{blocks['system_prompt']}
"""


def create_task(project_id: int, title: str, description: str, task_type: str, tags: str, context: str, uploaded_files) -> int:
    created_at = now_iso()
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO tasks (
                project_id, title, description, task_type, status, tags, context,
                uploads_json, suggested_model, router_summary, router_data_json,
                prompt_main, prompt_system, llm_output, useful_extract,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, 'borrador', ?, ?, '[]', '', '', '', '', '', '', '', ?, ?)
            """,
            (
                project_id,
                title.strip(),
                description.strip(),
                task_type,
                tags.strip(),
                context.strip(),
                created_at,
                created_at,
            ),
        )
        task_id = int(cur.lastrowid)

        project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        project_docs = conn.execute("SELECT * FROM project_documents WHERE project_id = ?", (project_id,)).fetchall()
        task_uploads = save_task_files(project_id, task_id, uploaded_files)

        router = score_model(task_type, title, description, context, project["base_context"], project_docs, task_uploads)
        router_summary = router_summary_from_data(router)
        task_payload = {
            "title": title,
            "description": description,
            "task_type": task_type,
            "context": context,
        }
        prompt_blocks = build_prompt_blocks(project, task_payload, router["recommended_model"], project_docs, task_uploads)

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
        md_path = write_task_markdown(project, row)
        conn.execute("UPDATE tasks SET markdown_path = ?, updated_at = ? WHERE id = ?", (md_path, now_iso(), task_id))
    return task_id


def update_task(
    task_id: int,
    project: sqlite3.Row,
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
) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE tasks
            SET title = ?, description = ?, task_type = ?, status = ?, tags = ?, context = ?,
                uploads_json = ?, suggested_model = ?, router_summary = ?, router_data_json = ?,
                prompt_main = ?, prompt_system = ?, llm_output = ?, useful_extract = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                title.strip(),
                description.strip(),
                task_type,
                status,
                tags.strip(),
                context.strip(),
                uploads_json,
                suggested_model,
                router_summary,
                router_data_json,
                prompt_main,
                prompt_system,
                llm_output,
                useful_extract,
                now_iso(),
                task_id,
            ),
        )
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        md_path = write_task_markdown(project, row)
        conn.execute("UPDATE tasks SET markdown_path = ?, updated_at = ? WHERE id = ?", (md_path, now_iso(), task_id))


def get_project_tasks(project_id: int, search: str = "", status_filter: str = "") -> List[sqlite3.Row]:
    query = "SELECT * FROM tasks WHERE project_id = ?"
    params = [project_id]
    if search.strip():
        query += " AND (title LIKE ? OR description LIKE ? OR tags LIKE ? OR context LIKE ?)"
        pattern = f"%{search.strip()}%"
        params += [pattern, pattern, pattern, pattern]
    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)
    query += " ORDER BY updated_at DESC, id DESC"
    with get_conn() as conn:
        return conn.execute(query, params).fetchall()


def get_task(task_id: int) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()


def create_asset(project_id: int, task_id: int, title: str, summary: str, content: str) -> int:
    created_at = now_iso()
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO assets (project_id, task_id, title, summary, content, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (project_id, task_id, title.strip(), summary.strip(), content.strip(), created_at),
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


def write_task_markdown(project: sqlite3.Row, task: sqlite3.Row | dict) -> str:
    path = task_markdown_path(int(task["id"]), str(task["title"]))
    content = f"""# {task["title"]}

- Proyecto: {project["name"]}
- ID tarea: {task["id"]}
- Tipo: {task["task_type"]}
- Estado: {task["status"]}
- Modelo recomendado: {task["suggested_model"]}
- Etiquetas: {task["tags"]}
- Creado: {task["created_at"]}
- Actualizado: {task["updated_at"]}

## Descripción
{task["description"]}

## Contexto del proyecto
{project["base_context"]}

## Contexto de la tarea
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
        .stApp {
            background: #F7F9FC;
            color: #0F172A;
        }
        .block-container {
            max-width: 1480px;
            padding-top: 1rem;
            padding-bottom: 1.6rem;
            padding-left: 1.4rem;
            padding-right: 1.4rem;
        }
        h1, h2, h3 {
            color: #0F172A;
            letter-spacing: -0.02em;
        }
        [data-testid="stSidebar"] {
            background: #FFFFFF;
            border-right: 1px solid #E2E8F0;
        }
        [data-testid="stSidebar"] * {
            color: #0F172A !important;
        }
        .panel, .card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 18px;
            padding: 1rem 1.1rem;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        }
        .card { margin-bottom: 0.9rem; }
        .muted {
            color: #475569;
            font-size: 0.92rem;
        }
        .meta {
            color: #94A3B8;
            font-size: 0.82rem;
        }
        .metric {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 16px;
            padding: 0.85rem 0.95rem;
        }
        .pill {
            display: inline-block;
            padding: 0.16rem 0.5rem;
            border-radius: 999px;
            border: 1px solid #E2E8F0;
            color: #475569;
            background: #FFFFFF;
            font-size: 0.76rem;
            margin-right: 0.35rem;
        }
        .project-row, .task-row {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 16px;
            padding: 0.9rem 0.95rem;
            margin-bottom: 0.75rem;
        }
        .task-row.selected {
            border: 2px solid #1E293B;
        }
        .stepper {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            margin-bottom: 1rem;
        }
        .step {
            padding: 0.5rem 0.75rem;
            border-radius: 999px;
            border: 1px solid #E2E8F0;
            background: #FFFFFF;
            color: #475569;
            font-size: 0.84rem;
            font-weight: 600;
        }
        .step.active {
            background: #1E293B;
            color: #FFFFFF;
            border-color: #1E293B;
        }
        .step.done {
            background: #F8FAFC;
            color: #475569;
            border-color: #E2E8F0;
        }
        .router-box {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 18px;
            padding: 1rem 1.1rem;
        }
        .router-model {
            font-size: 1.9rem;
            font-weight: 800;
            color: #0F172A;
            margin-top: 0.1rem;
        }
        .section-title {
            font-size: 0.95rem;
            font-weight: 700;
            color: #0F172A;
            margin-top: 0.35rem;
            margin-bottom: 0.35rem;
        }
        div[data-baseweb="select"] > div, .stTextInput input, .stTextArea textarea {
            border-radius: 12px !important;
            border: 1px solid #E2E8F0 !important;
            background: #FFFFFF !important;
            color: #0F172A !important;
        }
        div.stButton > button, .stDownloadButton > button, div[data-testid="stFormSubmitButton"] > button {
            border-radius: 12px !important;
            border: 1px solid #CBD5E1 !important;
            background: #FFFFFF !important;
            color: #0F172A !important;
            padding: 0.55rem 0.9rem !important;
            font-weight: 600 !important;
        }
        div.stButton > button:hover, .stDownloadButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
            border-color: #94A3B8 !important;
            background: #F8FAFC !important;
        }
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
                <div class="muted">Organiza el trabajo por proyecto, calcula el mejor modelo y convierte resultados en activos reutilizables.</div>
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
                    <span class="pill">{p["asset_count"]} activos</span>
                    <span class="pill">{p["status"]}</span>
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
        name = st.text_input("Nombre del proyecto", placeholder="Ej.: Portable Work Router")
        description = st.text_area("Descripción breve", placeholder="Qué es este proyecto.", height=90)
        objective = st.text_area("Objetivo", placeholder="Para qué existe el proyecto.", height=90)
        base_context = st.text_area("Contexto base", placeholder="Contexto estable del proyecto.", height=140)
        base_instructions = st.text_area("Instrucciones estables", placeholder="Reglas, estilo, restricciones o convenciones.", height=120)
        tags = st.text_input("Etiquetas", placeholder="pwr, producto, b2b")
        project_files = st.file_uploader(
            "Documentos del proyecto",
            accept_multiple_files=True,
            key="project_files",
            help="Documentos persistentes asociados al proyecto.",
        )

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
    tasks = get_project_tasks(project["id"])
    assets = get_project_assets(project["id"])

    st.markdown(
        f"""
        <div class="card">
            <div style="font-size:1.4rem;font-weight:700;">{project["name"]}</div>
            <div class="muted" style="margin-top:0.2rem;">{project["description"] or "Sin descripción."}</div>
            <div style="margin-top:0.55rem;">
                <span class="pill">{len(tasks)} tareas</span>
                <span class="pill">{len(assets)} activos</span>
                <span class="pill">{len(docs)} documentos</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_resumen, tab_tareas, tab_activos, tab_documentos = st.tabs(["Resumen", "Tareas", "Activos", "Documentos"])

    with tab_resumen:
        c1, c2 = st.columns([1.25, 1], gap="large")
        with c1:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown("### Contexto del proyecto")
            st.write(project["base_context"] or "Sin contexto base definido.")
            st.markdown("### Objetivo")
            st.write(project["objective"] or "Sin objetivo definido.")
            st.markdown("### Instrucciones estables")
            st.write(project["base_instructions"] or "Sin instrucciones adicionales.")
            st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown("### Actividad reciente")
            if tasks:
                for t in tasks[:5]:
                    st.markdown(f"- **{t['title']}** · {t['status']}")
            else:
                st.write("Todavía no hay tareas.")
            st.markdown('</div>', unsafe_allow_html=True)

    with tab_tareas:
        render_tasks_tab(project, docs)

    with tab_activos:
        if not assets:
            st.markdown('<div class="card">Todavía no hay activos creados en este proyecto.</div>', unsafe_allow_html=True)
        for a in assets:
            st.markdown(
                f"""
                <div class="card">
                    <div style="font-weight:700;">{a["title"]}</div>
                    <div class="muted" style="margin:0.2rem 0 0.45rem 0;">Procede de: {a["task_title"]}</div>
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


def render_tasks_tab(project: sqlite3.Row, project_docs: List[sqlite3.Row]) -> None:
    tasks = get_project_tasks(project["id"])
    selected_task_id = st.session_state.get("selected_task_id")
    if tasks and selected_task_id not in [int(t["id"]) for t in tasks]:
        selected_task_id = int(tasks[0]["id"])
        st.session_state["selected_task_id"] = selected_task_id

    left, right = st.columns([0.95, 2.05], gap="large")

    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("### Nueva tarea")
        title = st.text_input("Título", placeholder="Ej.: Revisar el routing del proyecto")
        task_type = st.selectbox("Tipo de trabajo", list(TIPOS_TAREA.keys()))
        tags = st.text_input("Etiquetas", placeholder="router, ux, prioridad")
        description = st.text_area("Descripción", placeholder="Qué necesitas conseguir.", height=100)
        context = st.text_area("Contexto específico", placeholder="Notas concretas de esta tarea.", height=130)
        task_files = st.file_uploader(
            "Documentos de la tarea",
            accept_multiple_files=True,
            key="task_files",
            help="Adjuntos específicos de esta tarea.",
        )
        if task_files:
            for f in task_files:
                st.markdown(f"- {f.name} ({human_size(f.size)})")
        if st.button("Crear tarea", use_container_width=True):
            if not title.strip() or not description.strip():
                st.error("Título y descripción son obligatorios.")
            else:
                task_id = create_task(project["id"], title, description, task_type, tags, context, task_files)
                st.session_state["selected_task_id"] = task_id
                st.session_state[f"step_{task_id}"] = "Router"
                st.success("Tarea creada.")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.write("")

        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("### Tareas del proyecto")
        search = st.text_input("Buscar en tus tareas", placeholder="Título, contenido o etiqueta", key=f"search_{project['id']}")
        status_filter = st.selectbox(
            "Estado",
            ["", *ESTADOS_TAREA],
            index=0,
            format_func=lambda x: "Todos" if x == "" else x,
            key=f"status_{project['id']}",
        )
        filtered = get_project_tasks(project["id"], search=search, status_filter=status_filter)
        if not filtered:
            st.write("No hay tareas con ese criterio.")
        for t in filtered:
            selected_class = " selected" if int(t["id"]) == selected_task_id else ""
            st.markdown(
                f"""
                <div class="task-row{selected_class}">
                    <div style="font-weight:700;">{t["title"]}</div>
                    <div class="muted" style="margin:0.2rem 0 0.45rem 0;">{t["description"][:90]}{"..." if len(t["description"]) > 90 else ""}</div>
                    <span class="pill">{t["task_type"]}</span>
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

        task_uploads = safe_json_loads(task["uploads_json"], [])
        current_step = st.session_state.get(f"step_{task['id']}", infer_step(task))
        st.session_state[f"step_{task['id']}"] = current_step

        router_data = safe_json_loads(task["router_data_json"], {})
        if not router_data:
            router_data = score_model(task["task_type"], task["title"], task["description"], task["context"], project["base_context"], project_docs, task_uploads)

        prompt_blocks = build_prompt_blocks(
            project,
            {
                "title": task["title"],
                "description": task["description"],
                "task_type": task["task_type"],
                "context": task["context"],
            },
            task["suggested_model"] or router_data["recommended_model"],
            project_docs,
            task_uploads,
        )
        full_prompt = export_full_prompt(prompt_blocks)

        st.markdown(
            f"""
            <div class="card">
                <div style="font-size:1.15rem;font-weight:700;">{task["title"]}</div>
                <div class="muted">{task["description"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_stepper(current_step)

        if current_step == "Tarea":
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            title = st.text_input("Título de la tarea", value=task["title"], key=f"title_{task['id']}")
            c1, c2, c3 = st.columns(3)
            with c1:
                task_type = st.selectbox("Tipo de trabajo", list(TIPOS_TAREA.keys()), index=list(TIPOS_TAREA.keys()).index(task["task_type"]), key=f"type_{task['id']}")
            with c2:
                status = st.selectbox("Estado", ESTADOS_TAREA, index=ESTADOS_TAREA.index(task["status"]) if task["status"] in ESTADOS_TAREA else 0, key=f"status_task_{task['id']}")
            with c3:
                tags = st.text_input("Etiquetas", value=task["tags"], key=f"tags_{task['id']}")
            description = st.text_area("Descripción", value=task["description"], height=100, key=f"desc_{task['id']}")
            context = st.text_area("Contexto específico", value=task["context"], height=220, key=f"ctx_{task['id']}")
            if task_uploads:
                st.markdown("**Documentos asociados a la tarea**")
                for d in task_uploads:
                    st.markdown(f"- {d['name']} ({human_size(d['size'])})")
            b1, b2 = st.columns(2)
            with b1:
                if st.button("Guardar tarea", use_container_width=True, key=f"save_task_{task['id']}"):
                    new_router = score_model(task_type, title, description, context, project["base_context"], project_docs, task_uploads)
                    new_summary = router_summary_from_data(new_router)
                    new_blocks = build_prompt_blocks(
                        project,
                        {"title": title, "description": description, "task_type": task_type, "context": context},
                        new_router["recommended_model"],
                        project_docs,
                        task_uploads,
                    )
                    update_task(
                        int(task["id"]), project, title, description, task_type, status, tags, context,
                        task["uploads_json"], new_router["recommended_model"], new_summary,
                        json.dumps(new_router, ensure_ascii=False), new_blocks["main_prompt"],
                        new_blocks["system_prompt"], task["llm_output"], task["useful_extract"]
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
                    new_router = score_model(task["task_type"], task["title"], task["description"], task["context"], project["base_context"], project_docs, task_uploads)
                    new_summary = router_summary_from_data(new_router)
                    new_blocks = build_prompt_blocks(
                        project,
                        {"title": task["title"], "description": task["description"], "task_type": task["task_type"], "context": task["context"]},
                        new_router["recommended_model"],
                        project_docs,
                        task_uploads,
                    )
                    update_task(
                        int(task["id"]), project, task["title"], task["description"], task["task_type"], "router_listo", task["tags"], task["context"],
                        task["uploads_json"], new_router["recommended_model"], new_summary,
                        json.dumps(new_router, ensure_ascii=False), new_blocks["main_prompt"],
                        new_blocks["system_prompt"], task["llm_output"], task["useful_extract"]
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

            with st.expander("Ver contexto del proyecto"):
                st.text_area("Contexto del proyecto", value=prompt_blocks["project_context"], height=180, disabled=True, label_visibility="collapsed")
            with st.expander("Ver contexto de la tarea"):
                st.text_area("Contexto de la tarea", value=prompt_blocks["task_context"], height=160, disabled=True, label_visibility="collapsed")
            with st.expander("Ver documentos del proyecto"):
                st.text_area("Documentos del proyecto", value=prompt_blocks["project_documents"], height=120, disabled=True, label_visibility="collapsed")
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
                        int(task["id"]), project, task["title"], task["description"], task["task_type"], "ejecutado", task["tags"], task["context"],
                        task["uploads_json"], task["suggested_model"], task["router_summary"], task["router_data_json"],
                        task["prompt_main"], task["prompt_system"], llm_output, useful_extract
                    )
                    st.success("Resultado guardado.")
                    st.rerun()
            with b3:
                if st.button("Siguiente: activo", use_container_width=True, key=f"next_asset_{task['id']}"):
                    update_task(
                        int(task["id"]), project, task["title"], task["description"], task["task_type"], "ejecutado", task["tags"], task["context"],
                        task["uploads_json"], task["suggested_model"], task["router_summary"], task["router_data_json"],
                        task["prompt_main"], task["prompt_system"], llm_output, useful_extract
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
                        create_asset(project["id"], int(task["id"]), asset_title, asset_summary, asset_content)
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
        st.caption("Diseño sobrio · castellano · trabajo por proyecto")

    render_topbar()
    st.write("")

    if page == "Proyectos":
        view_projects()
    else:
        view_project_workspace()


if __name__ == "__main__":
    main()
