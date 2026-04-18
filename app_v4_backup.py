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
TASKS_DIR = DATA_DIR / "tasks"
ASSETS_DIR = DATA_DIR / "assets"
UPLOADS_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "pwr.db"

TASK_TYPES = {
    "Pensar": "Trabajo de exploración, framing o análisis general",
    "Escribir": "Redacción estructurada, narrativa, posicionamiento o contenido",
    "Programar": "Código, debugging, arquitectura técnica o scripts",
    "Revisar": "Crítica, revisión, evaluación o QA",
    "Decidir": "Comparar opciones, priorizar o tomar una decisión",
}
STATUS_OPTIONS = ["borrador", "router_listo", "ejecutado", "archivado"]
STEP_ORDER = ["Tarea", "Router", "Prompt", "Resultado", "Activo"]

MODEL_LABELS = {
    "Claude": "Claude",
    "ChatGPT": "ChatGPT",
    "Codex": "Codex",
    "Gemini": "Gemini",
}


def ensure_dirs() -> None:
    DATA_DIR.mkdir(exist_ok=True)
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
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                task_type TEXT NOT NULL,
                context TEXT DEFAULT '',
                suggested_model TEXT DEFAULT '',
                router_summary TEXT DEFAULT '',
                router_data_json TEXT DEFAULT '',
                prompt_main TEXT DEFAULT '',
                prompt_system TEXT DEFAULT '',
                llm_output TEXT DEFAULT '',
                useful_extract TEXT DEFAULT '',
                status TEXT DEFAULT 'borrador',
                tags TEXT DEFAULT '',
                uploads_json TEXT DEFAULT '[]',
                markdown_path TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                summary TEXT DEFAULT '',
                content TEXT NOT NULL,
                markdown_path TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY(task_id) REFERENCES tasks(id)
            )
            """
        )

        cols = [row["name"] for row in conn.execute("PRAGMA table_info(tasks)").fetchall()]
        migrations = {
            "router_summary": "ALTER TABLE tasks ADD COLUMN router_summary TEXT DEFAULT ''",
            "router_data_json": "ALTER TABLE tasks ADD COLUMN router_data_json TEXT DEFAULT ''",
            "prompt_main": "ALTER TABLE tasks ADD COLUMN prompt_main TEXT DEFAULT ''",
            "prompt_system": "ALTER TABLE tasks ADD COLUMN prompt_system TEXT DEFAULT ''",
            "uploads_json": "ALTER TABLE tasks ADD COLUMN uploads_json TEXT DEFAULT '[]'",
        }
        for col, sql in migrations.items():
            if col not in cols:
                conn.execute(sql)


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def slugify(text: str) -> str:
    safe = "".join(ch.lower() if ch.isalnum() else "-" for ch in text.strip())
    while "--" in safe:
        safe = safe.replace("--", "-")
    return safe.strip("-")[:80] or "item"


def task_markdown_path(task_id: int, title: str) -> Path:
    return TASKS_DIR / f"{task_id:04d}-{slugify(title)}.md"


def asset_markdown_path(asset_id: int, title: str) -> Path:
    return ASSETS_DIR / f"{asset_id:04d}-{slugify(title)}.md"


def safe_json_loads(value: str, default):
    try:
        return json.loads(value) if value else default
    except Exception:
        return default


def save_uploaded_files(task_id: int, files) -> List[Dict]:
    saved = []
    task_upload_dir = UPLOADS_DIR / f"task_{task_id:04d}"
    task_upload_dir.mkdir(parents=True, exist_ok=True)

    for f in files or []:
        name = Path(f.name).name
        target = task_upload_dir / name
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


def human_size(num_bytes: int) -> str:
    if num_bytes < 1024:
        return f"{num_bytes} B"
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    return f"{num_bytes / (1024 * 1024):.1f} MB"


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


def score_model(task_type: str, title: str, description: str, context: str, uploads: List[Dict]) -> Dict:
    text = f"{title} {description} {context}".lower()
    scores = {"Claude": 0, "ChatGPT": 0, "Codex": 0, "Gemini": 0}

    signals = []

    def add(model: str, points: int, reason: str, metric: str):
        scores[model] += points
        signals.append({"model": model, "points": points, "reason": reason, "metric": metric})

    # Base by task type
    if task_type == "Escribir":
        add("Claude", 5, "La tarea exige redacción estructurada, claridad narrativa y buena organización.", "estructura")
        add("ChatGPT", 2, "Puede servir para iterar variantes o desbloquear rápidamente.", "velocidad")
    elif task_type == "Pensar":
        add("ChatGPT", 4, "La tarea parece de exploración amplia o framing inicial.", "exploración")
        add("Claude", 3, "Aporta más profundidad y orden cuando la reflexión debe quedar articulada.", "profundidad")
    elif task_type == "Programar":
        add("Codex", 7, "La tarea está más cerca de código, debugging o implementación técnica.", "código")
        add("ChatGPT", 1, "Puede apoyar con contraste rápido o explicación.", "apoyo")
    elif task_type == "Revisar":
        add("Claude", 4, "La revisión se beneficia de lectura cuidadosa y respuesta bien argumentada.", "revisión")
        add("ChatGPT", 2, "Puede contrastar o resumir rápidamente.", "contraste")
    elif task_type == "Decidir":
        add("ChatGPT", 4, "La tarea pide comparar opciones y avanzar rápido sobre alternativas.", "decisión")
        add("Claude", 2, "Puede ordenar mejor trade-offs complejos.", "trade-offs")

    context_len = len(context.strip())
    if context_len > 350:
        add("Claude", 2, "Hay bastante contexto y conviene un modelo cómodo con entradas largas.", "contexto")
    if context_len > 900:
        add("Claude", 2, "El volumen de contexto es alto y favorece profundidad sobre velocidad.", "contexto_extenso")

    if uploads:
        add("Claude", 2, "Hay documentos adjuntos y conviene priorizar una lectura más estructurada.", "documentos")
        add("Gemini", 1, "Puede ser útil como segunda lectura o contraste con material adjunto.", "contraste_documental")

    strategic_terms = ["estrateg", "marca", "mensaje", "narrativa", "posicion", "editorial", "roadmap", "stakeholder"]
    if any(k in text for k in strategic_terms):
        add("Claude", 2, "Aparece una capa estratégica o editorial relevante.", "estrategia")

    technical_terms = ["python", "script", "api", "sql", "streamlit", "bug", "backend", "frontend", "deploy", "docker"]
    if any(k in text for k in technical_terms):
        add("Codex", 3, "Hay señales claras de trabajo técnico o de programación.", "señales_técnicas")

    compare_terms = ["comparar", "alternativas", "opciones", "ideas", "brainstorm", "hipótesis", "hipotesis"]
    if any(k in text for k in compare_terms):
        add("ChatGPT", 2, "Conviene explorar opciones con agilidad.", "opciones")
        add("Gemini", 1, "Puede servir como segunda opinión.", "segunda_opinión")

    verification_terms = ["validar", "verificar", "confirmar", "contrastar", "segunda opinión", "segunda opinion"]
    if any(k in text for k in verification_terms):
        add("Gemini", 2, "La tarea menciona contraste o validación explícita.", "validación")

    ranking = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    recommended = ranking[0][0]
    second = ranking[1][0]
    gap = ranking[0][1] - ranking[1][1]

    fit = "alto" if gap >= 3 else "medio" if gap >= 1 else "ajustado"
    model_signals = [s for s in signals if s["model"] == recommended]
    model_signals = sorted(model_signals, key=lambda s: s["points"], reverse=True)[:4]

    alternative_explanations = []
    for model, _ in ranking[1:4]:
        if model == recommended:
            continue
        why_not = [s["reason"] for s in signals if s["model"] == model][:2]
        if not why_not:
            why_not = ["Puede servir como alternativa, pero no es la primera opción con las señales actuales."]
        alternative_explanations.append({"model": model, "notes": why_not})

    return {
        "recommended_model": recommended,
        "fit": fit,
        "scores": scores,
        "primary_signals": model_signals,
        "alternatives": alternative_explanations,
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


def build_prompt_blocks(title: str, description: str, task_type: str, context: str, suggested_model: str, uploads: List[Dict]):
    system_prompt = """Actúa como un colaborador experto y riguroso.
Prioriza claridad, criterio, estructura y utilidad práctica.
No rellenes. No repitas información innecesaria.
Si detectas ambigüedad, propón la mejor interpretación operativa y sigue adelante."""

    docs_section = "No hay documentos adjuntos."
    if uploads:
        docs_lines = []
        for item in uploads:
            docs_lines.append(f"- {item['name']} ({human_size(item.get('size', 0))})")
        docs_section = "\n".join(docs_lines)

    main_prompt = f"""TAREA
{title}

TIPO DE TRABAJO
{task_type}

MODELO RECOMENDADO
{suggested_model}

OBJETIVO
{description}

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
        "context_summary": (context[:700] + "...") if len(context) > 700 else (context or "Sin contexto adicional."),
        "full_context": context or "Sin contexto adicional.",
        "documents_summary": docs_section,
        "system_prompt": system_prompt,
    }


def export_full_prompt(blocks: Dict) -> str:
    return f"""{blocks['main_prompt']}

CONTEXTO RESUMIDO
{blocks['context_summary']}

DOCUMENTOS ADJUNTOS
{blocks['documents_summary']}

INSTRUCCIONES DEL SISTEMA
{blocks['system_prompt']}
"""


def write_task_markdown(task: sqlite3.Row | dict) -> str:
    path = task_markdown_path(int(task["id"]), str(task["title"]))
    content = f"""# {task["title"]}

- ID: {task["id"]}
- Tipo: {task["task_type"]}
- Modelo recomendado: {task["suggested_model"]}
- Estado: {task["status"]}
- Tags: {task["tags"]}
- Creado: {task["created_at"]}
- Actualizado: {task["updated_at"]}

## Descripción
{task["description"]}

## Contexto
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

- Asset ID: {asset["id"]}
- Task ID: {asset["task_id"]}
- Creado: {asset["created_at"]}

## Resumen
{asset["summary"]}

## Contenido
{asset["content"]}
"""
    path.write_text(content, encoding="utf-8")
    return str(path)


def create_task(title: str, description: str, task_type: str, context: str, tags: str, uploaded_files) -> int:
    created_at = now_iso()
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO tasks (
                title, description, task_type, context, suggested_model,
                router_summary, router_data_json, prompt_main, prompt_system,
                status, tags, uploads_json, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                title.strip(),
                description.strip(),
                task_type,
                context.strip(),
                "",
                "",
                "",
                "",
                "",
                "borrador",
                tags.strip(),
                "[]",
                created_at,
                created_at,
            ),
        )
        task_id = int(cur.lastrowid)

        uploads = save_uploaded_files(task_id, uploaded_files)
        router = score_model(task_type, title, description, context, uploads)
        router_summary = router_summary_from_data(router)
        prompt_blocks = build_prompt_blocks(title, description, task_type, context, router["recommended_model"], uploads)

        conn.execute(
            """
            UPDATE tasks
            SET suggested_model = ?, router_summary = ?, router_data_json = ?, prompt_main = ?, prompt_system = ?,
                status = ?, uploads_json = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                router["recommended_model"],
                router_summary,
                json.dumps(router, ensure_ascii=False),
                prompt_blocks["main_prompt"],
                prompt_blocks["system_prompt"],
                "router_listo",
                json.dumps(uploads, ensure_ascii=False),
                now_iso(),
                task_id,
            ),
        )

        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        md_path = write_task_markdown(row)
        conn.execute("UPDATE tasks SET markdown_path = ?, updated_at = ? WHERE id = ?", (md_path, now_iso(), task_id))
    return task_id


def update_task(
    task_id: int,
    title: str,
    description: str,
    task_type: str,
    context: str,
    suggested_model: str,
    router_summary: str,
    router_data_json: str,
    prompt_main: str,
    prompt_system: str,
    llm_output: str,
    useful_extract: str,
    status: str,
    tags: str,
    uploads_json: str,
) -> None:
    updated_at = now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE tasks
            SET title = ?, description = ?, task_type = ?, context = ?, suggested_model = ?,
                router_summary = ?, router_data_json = ?, prompt_main = ?, prompt_system = ?,
                llm_output = ?, useful_extract = ?, status = ?, tags = ?, uploads_json = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                title.strip(),
                description.strip(),
                task_type,
                context.strip(),
                suggested_model.strip(),
                router_summary,
                router_data_json,
                prompt_main,
                prompt_system,
                llm_output,
                useful_extract,
                status,
                tags.strip(),
                uploads_json,
                updated_at,
                task_id,
            ),
        )
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        md_path = write_task_markdown(row)
        conn.execute("UPDATE tasks SET markdown_path = ?, updated_at = ? WHERE id = ?", (md_path, now_iso(), task_id))


def get_tasks(search: str = "", only_status: str = "") -> List[sqlite3.Row]:
    query = "SELECT * FROM tasks"
    clauses = []
    params = []

    if search.strip():
        clauses.append("(title LIKE ? OR description LIKE ? OR tags LIKE ? OR context LIKE ?)")
        pattern = f"%{search.strip()}%"
        params += [pattern, pattern, pattern, pattern]

    if only_status:
        clauses.append("status = ?")
        params.append(only_status)

    if clauses:
        query += " WHERE " + " AND ".join(clauses)

    query += " ORDER BY updated_at DESC, id DESC"
    with get_conn() as conn:
        return conn.execute(query, params).fetchall()


def get_task(task_id: int) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()


def create_asset(task_id: int, title: str, summary: str, content: str) -> int:
    created_at = now_iso()
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO assets (task_id, title, summary, content, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (task_id, title.strip(), summary.strip(), content.strip(), created_at),
        )
        asset_id = int(cur.lastrowid)
        row = conn.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
        md_path = write_asset_markdown(row)
        conn.execute("UPDATE assets SET markdown_path = ? WHERE id = ?", (md_path, asset_id))
    return asset_id


def get_assets() -> List[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT a.*, t.title AS task_title
            FROM assets a
            JOIN tasks t ON a.task_id = t.id
            ORDER BY a.created_at DESC, a.id DESC
            """
        ).fetchall()


def stats() -> Dict[str, int]:
    with get_conn() as conn:
        task_count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        asset_count = conn.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
        active_count = conn.execute("SELECT COUNT(*) FROM tasks WHERE status IN ('router_listo','ejecutado')").fetchone()[0]
    return {"tasks": task_count, "assets": asset_count, "active": active_count}


def inject_css() -> None:
    st.markdown(
        """
        <style>
        .stApp { background: #f5f7fb; color: #162033; }
        .block-container { max-width: 1460px; padding-top: 1rem; padding-bottom: 1.8rem; padding-left: 1.4rem; padding-right: 1.4rem; }
        h1, h2, h3 { letter-spacing: -0.02em; color: #162033; }
        [data-testid="stSidebar"] { background: #eef3fb; border-right: 1px solid #d7deea; }
        [data-testid="stSidebar"] * { color: #162033 !important; }
        .soft-card, .panel-card {
            padding: 1rem 1.1rem; border: 1px solid #dbe3ef; background: #fff;
            border-radius: 18px; box-shadow: 0 1px 2px rgba(16,24,40,.04);
        }
        .soft-card { margin-bottom: 1rem; }
        .muted { color: #5f6f89; font-size: .92rem; }
        .metric {
            padding: .9rem 1rem; border-radius: 16px; background: #fff; border: 1px solid #dbe3ef;
            box-shadow: 0 1px 2px rgba(16,24,40,.04);
        }
        .item-title { font-weight: 700; font-size: 1.02rem; margin-bottom: .2rem; color: #162033; }
        .pill {
            display: inline-block; padding: .18rem .55rem; border-radius: 999px; background: #eef3fb;
            border: 1px solid #d7deea; color: #33415c; margin-right: .35rem; font-size: .76rem;
        }
        .task-row {
            padding: .85rem .95rem; border: 1px solid #dbe3ef; background: #fff;
            border-radius: 16px; margin-bottom: .75rem;
        }
        .task-row.selected { border: 2px solid #6b8ac9; box-shadow: 0 0 0 3px rgba(107,138,201,.10); }
        .empty {
            padding: 2rem 1.2rem; border-radius: 18px; text-align: center;
            border: 1px dashed #c9d4e5; background: #fff; color: #5f6f89;
        }
        .stepper { display: flex; gap: .55rem; flex-wrap: wrap; margin-bottom: 1rem; }
        .step {
            padding: .55rem .8rem; border-radius: 999px; border: 1px solid #d7deea;
            background: #fff; color: #5f6f89; font-size: .85rem; font-weight: 600;
        }
        .step.active { background: #162033; color: #fff; border-color: #162033; }
        .step.done { background: #eef6ef; color: #2f6f44; border-color: #b9d8c2; }
        .router-card {
            padding: 1.15rem 1.2rem; border-radius: 20px; background: linear-gradient(135deg, #18253b 0%, #243a5d 100%);
            color: #fff; border: 1px solid #223b63; box-shadow: 0 10px 24px rgba(27,43,70,.18);
        }
        .router-card * { color: #fff !important; }
        .router-badge {
            display: inline-block; padding: .22rem .6rem; border-radius: 999px; background: rgba(255,255,255,.12);
            border: 1px solid rgba(255,255,255,.18); margin-right: .35rem; font-size: .78rem;
        }
        .section-title { font-size: .95rem; font-weight: 700; color: #33415c; margin-top: .3rem; margin-bottom: .35rem; }
        div[data-baseweb="select"] > div, .stTextInput input, .stTextArea textarea {
            border-radius: 12px !important; border: 1px solid #cfd8e6 !important; background: #fff !important; color: #162033 !important;
        }
        div.stButton > button, .stDownloadButton > button, div[data-testid="stFormSubmitButton"] > button {
            border-radius: 12px !important; border: 1px solid #cfd8e6 !important; background: #fff !important;
            color: #162033 !important; padding: .55rem .9rem !important; font-weight: 600 !important;
        }
        div.stButton > button:hover, .stDownloadButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
            border-color: #94a8c6 !important; background: #f8fbff !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_topbar() -> None:
    s = stats()
    c1, c2 = st.columns([2.2, 1.4])
    with c1:
        st.markdown(
            """
            <div class="soft-card">
                <h1 style="margin:0;">Portable Work Router</h1>
                <div class="muted">Transforma una tarea difusa en una recomendación de modelo, un prompt operativo y un activo portable.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        mc1, mc2, mc3 = st.columns(3)
        mc1.markdown(f'<div class="metric"><div class="muted">Tareas</div><div style="font-size:1.42rem;font-weight:700;">{s["tasks"]}</div></div>', unsafe_allow_html=True)
        mc2.markdown(f'<div class="metric"><div class="muted">Activos</div><div style="font-size:1.42rem;font-weight:700;">{s["assets"]}</div></div>', unsafe_allow_html=True)
        mc3.markdown(f'<div class="metric"><div class="muted">Activas</div><div style="font-size:1.42rem;font-weight:700;">{s["active"]}</div></div>', unsafe_allow_html=True)


def render_stepper(current_step: str) -> None:
    current_index = STEP_ORDER.index(current_step)
    parts = []
    for i, step in enumerate(STEP_ORDER):
        cls = "step"
        if i < current_index:
            cls += " done"
        elif i == current_index:
            cls += " active"
        parts.append(f'<div class="{cls}">{i+1}. {step}</div>')
    st.markdown('<div class="stepper">' + "".join(parts) + '</div>', unsafe_allow_html=True)


def ensure_selected_task(rows: List[sqlite3.Row]) -> Optional[int]:
    if not rows:
        return None
    selected = st.session_state.get("selected_task_id")
    valid_ids = [int(r["id"]) for r in rows]
    if selected not in valid_ids:
        st.session_state["selected_task_id"] = valid_ids[0]
    return st.session_state["selected_task_id"]


def render_task_list(rows: List[sqlite3.Row], selected_id: Optional[int]) -> None:
    if not rows:
        st.markdown('<div class="empty">Todavía no hay tareas.</div>', unsafe_allow_html=True)
        return
    for row in rows:
        selected_class = " selected" if int(row["id"]) == selected_id else ""
        step = infer_step(row)
        st.markdown(
            f"""
            <div class="task-row{selected_class}">
                <div class="item-title">{row["title"]}</div>
                <div class="muted" style="margin-bottom:0.45rem;">{row["description"][:95]}{"..." if len(row["description"]) > 95 else ""}</div>
                <span class="pill">{row["task_type"]}</span>
                <span class="pill">{step}</span>
                <span class="pill">{row["suggested_model"] or "Sin router"}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(f"Abrir #{row['id']}", key=f"task_pick_{row['id']}", use_container_width=True):
            st.session_state["selected_task_id"] = int(row["id"])
            st.rerun()


def create_quick_task_block() -> None:
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.subheader("Entrada rápida")
    render_stepper("Tarea")
    title = st.text_input("¿Qué quieres hacer?", placeholder="Ej.: Preparar briefing para rediseño de onboarding")
    c1, c2 = st.columns([1, 1])
    with c1:
        task_type = st.selectbox("Tipo de trabajo", list(TASK_TYPES.keys()))
    with c2:
        tags = st.text_input("Etiquetas", placeholder="pwr, ux, onboarding")
    description = st.text_area("Descripción breve", placeholder="Qué necesitas conseguir con esta tarea.", height=110)
    context = st.text_area("Contexto inicial", placeholder="Antecedentes, restricciones, notas o criterios.", height=150)
    uploaded_files = st.file_uploader(
        "Adjuntar documentos de referencia",
        accept_multiple_files=True,
        key="quick_uploader",
        help="Puedes adjuntar documentos para que formen parte del contexto de la tarea.",
    )

    if uploaded_files:
        st.markdown("**Documentos adjuntos**")
        for f in uploaded_files:
            st.markdown(f"- {f.name} ({human_size(f.size)})")

    if st.button("Crear tarea y calcular router", use_container_width=True):
        if not title.strip() or not description.strip():
            st.error("Título y descripción son obligatorios.")
        else:
            task_id = create_task(title, description, task_type, context, tags, uploaded_files)
            st.session_state["selected_task_id"] = task_id
            st.session_state[f"step_{task_id}"] = "Router"
            st.success("Tarea creada.")
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


def view_inbox() -> None:
    create_quick_task_block()
    st.write("")
    st.subheader("Tareas recientes")
    search = st.text_input("Buscar en tus tareas", placeholder="Título, contenido o etiqueta")
    rows = get_tasks(search=search)
    render_task_list(rows, st.session_state.get("selected_task_id"))


def view_workspace() -> None:
    rows = get_tasks()
    if not rows:
        st.markdown('<div class="empty">Crea primero una tarea en la pestaña Inbox para empezar.</div>', unsafe_allow_html=True)
        return

    selected_id = ensure_selected_task(rows)
    if selected_id is None:
        return

    task = get_task(int(selected_id))
    if task is None:
        st.warning("No se pudo cargar la tarea.")
        return

    left, right = st.columns([0.88, 2.12], gap="large")
    current_step = st.session_state.get(f"step_{selected_id}", infer_step(task))
    st.session_state[f"step_{selected_id}"] = current_step

    with left:
        st.subheader("Tareas")
        search = st.text_input("Buscar en tus tareas", placeholder="Título, contenido o etiqueta", key="workspace_search")
        status_filter = st.selectbox(
            "Estado",
            ["", *STATUS_OPTIONS],
            index=0,
            format_func=lambda x: "Todos" if x == "" else x,
            key="workspace_status",
        )
        render_task_list(get_tasks(search=search, only_status=status_filter) or rows, selected_id)

    with right:
        st.subheader("Workspace")
        render_stepper(current_step)

        uploads = safe_json_loads(task["uploads_json"], [])
        router_data = safe_json_loads(task["router_data_json"], {})
        if not router_data:
            router_data = score_model(task["task_type"], task["title"], task["description"], task["context"], uploads)
        prompt_blocks = build_prompt_blocks(task["title"], task["description"], task["task_type"], task["context"], task["suggested_model"] or router_data["recommended_model"], uploads)
        full_prompt = export_full_prompt(prompt_blocks)

        if current_step == "Tarea":
            st.markdown('<div class="panel-card">', unsafe_allow_html=True)
            title = st.text_input("Título", value=task["title"])
            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                task_type = st.selectbox("Tipo de trabajo", list(TASK_TYPES.keys()), index=list(TASK_TYPES.keys()).index(task["task_type"]))
            with c2:
                status = st.selectbox("Estado", STATUS_OPTIONS, index=STATUS_OPTIONS.index(task["status"]) if task["status"] in STATUS_OPTIONS else 0)
            with c3:
                tags = st.text_input("Etiquetas", value=task["tags"])
            description = st.text_area("Descripción", value=task["description"], height=110)
            context = st.text_area("Contexto", value=task["context"], height=260)

            if uploads:
                st.markdown("**Documentos actualmente asociados a la tarea**")
                for item in uploads:
                    st.markdown(f"- {item['name']} ({human_size(item.get('size', 0))})")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("Guardar cambios", use_container_width=True):
                    new_router = score_model(task_type, title, description, context, uploads)
                    new_summary = router_summary_from_data(new_router)
                    blocks = build_prompt_blocks(title, description, task_type, context, new_router["recommended_model"], uploads)
                    update_task(
                        int(selected_id),
                        title,
                        description,
                        task_type,
                        context,
                        new_router["recommended_model"],
                        new_summary,
                        json.dumps(new_router, ensure_ascii=False),
                        blocks["main_prompt"],
                        blocks["system_prompt"],
                        task["llm_output"],
                        task["useful_extract"],
                        status,
                        tags,
                        task["uploads_json"],
                    )
                    st.success("Tarea guardada.")
                    st.rerun()
            with c2:
                if st.button("Siguiente: router", use_container_width=True):
                    st.session_state[f"step_{selected_id}"] = "Router"
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        elif current_step == "Router":
            st.markdown(
                f"""
                <div class="router-card">
                    <div style="font-size:.9rem;opacity:.8;">Recomendación de modelo</div>
                    <div style="font-size:2rem;font-weight:800;margin-top:.1rem;">{router_data['recommended_model']}</div>
                    <div style="margin-top:.45rem;">Nivel de ajuste: <strong>{router_data['fit']}</strong></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.write("")
            c1, c2 = st.columns([1.35, 1])
            with c1:
                st.markdown("### Justificación técnica")
                st.markdown(
                    f"""
                    <div class="soft-card">
                        <div class="muted">La recomendación se basa en señales detectadas en la tarea, no en una preferencia arbitraria.</div>
                        <ul>
                            {"".join([f"<li><strong>{s['metric'].replace('_',' ').capitalize()}:</strong> {s['reason']}</li>" for s in router_data['primary_signals']])}
                        </ul>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.markdown("### Puntuación comparada")
                score_lines = []
                for model, score in sorted(router_data["scores"].items(), key=lambda x: x[1], reverse=True):
                    score_lines.append(f"- **{model}**: {score}")
                st.markdown("\n".join(score_lines))
            with c2:
                st.markdown("### Por qué no los otros")
                for alt in router_data["alternatives"]:
                    st.markdown(
                        f"""
                        <div class="soft-card">
                            <div class="item-title">{alt['model']}</div>
                            <div class="muted">{" ".join(alt['notes'])}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            b1, b2, b3 = st.columns(3)
            with b1:
                if st.button("Volver a tarea", use_container_width=True):
                    st.session_state[f"step_{selected_id}"] = "Tarea"
                    st.rerun()
            with b2:
                if st.button("Recalcular router", use_container_width=True):
                    new_router = score_model(task["task_type"], task["title"], task["description"], task["context"], uploads)
                    new_summary = router_summary_from_data(new_router)
                    blocks = build_prompt_blocks(task["title"], task["description"], task["task_type"], task["context"], new_router["recommended_model"], uploads)
                    update_task(
                        int(selected_id),
                        task["title"],
                        task["description"],
                        task["task_type"],
                        task["context"],
                        new_router["recommended_model"],
                        new_summary,
                        json.dumps(new_router, ensure_ascii=False),
                        blocks["main_prompt"],
                        blocks["system_prompt"],
                        task["llm_output"],
                        task["useful_extract"],
                        "router_listo",
                        task["tags"],
                        task["uploads_json"],
                    )
                    st.success("Router recalculado.")
                    st.rerun()
            with b3:
                if st.button("Aceptar y seguir al prompt", use_container_width=True):
                    st.session_state[f"step_{selected_id}"] = "Prompt"
                    st.rerun()

        elif current_step == "Prompt":
            st.markdown('<div class="panel-card">', unsafe_allow_html=True)
            st.markdown("### Prompt listo para usar")
            st.code(prompt_blocks["main_prompt"], language="markdown")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.download_button(
                    "Exportar prompt",
                    data=full_prompt,
                    file_name=f"prompt-task-{selected_id}.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
            with c2:
                if st.button("Volver al router", use_container_width=True):
                    st.session_state[f"step_{selected_id}"] = "Router"
                    st.rerun()
            with c3:
                if st.button("Ya tengo el resultado", use_container_width=True):
                    st.session_state[f"step_{selected_id}"] = "Resultado"
                    st.rerun()

            with st.expander("Ver contexto completo"):
                st.text_area("Contexto completo", value=prompt_blocks["full_context"], height=220, disabled=True, label_visibility="collapsed")
            with st.expander("Ver documentos adjuntos"):
                st.text_area("Documentos adjuntos", value=prompt_blocks["documents_summary"], height=120, disabled=True, label_visibility="collapsed")
            with st.expander("Ver instrucciones del sistema"):
                st.text_area("Instrucciones del sistema", value=prompt_blocks["system_prompt"], height=140, disabled=True, label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)

        elif current_step == "Resultado":
            st.markdown('<div class="panel-card">', unsafe_allow_html=True)
            llm_output = st.text_area("Resultado del modelo", value=task["llm_output"], height=280)
            useful_extract = st.text_area("Extracto reusable", value=task["useful_extract"], height=220)
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("Volver al prompt", use_container_width=True):
                    st.session_state[f"step_{selected_id}"] = "Prompt"
                    st.rerun()
            with c2:
                if st.button("Guardar resultado", use_container_width=True):
                    update_task(
                        int(selected_id),
                        task["title"], task["description"], task["task_type"], task["context"],
                        task["suggested_model"], task["router_summary"], task["router_data_json"],
                        task["prompt_main"], task["prompt_system"], llm_output, useful_extract,
                        "ejecutado", task["tags"], task["uploads_json"]
                    )
                    st.success("Resultado guardado.")
                    st.rerun()
            with c3:
                if st.button("Siguiente: activo", use_container_width=True):
                    update_task(
                        int(selected_id),
                        task["title"], task["description"], task["task_type"], task["context"],
                        task["suggested_model"], task["router_summary"], task["router_data_json"],
                        task["prompt_main"], task["prompt_system"], llm_output, useful_extract,
                        "ejecutado", task["tags"], task["uploads_json"]
                    )
                    st.session_state[f"step_{selected_id}"] = "Activo"
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        elif current_step == "Activo":
            default_content = task["useful_extract"].strip() or task["llm_output"].strip()
            st.markdown('<div class="panel-card">', unsafe_allow_html=True)
            asset_title = st.text_input("Título del activo", value=f"Activo · {task['title']}")
            asset_summary = st.text_area("Resumen", value=task["description"], height=90)
            asset_content = st.text_area("Contenido final", value=default_content, height=260)
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("Volver al resultado", use_container_width=True):
                    st.session_state[f"step_{selected_id}"] = "Resultado"
                    st.rerun()
            with c2:
                if st.button("Crear activo", use_container_width=True):
                    if not asset_content.strip():
                        st.error("No hay contenido para convertir en activo.")
                    else:
                        create_asset(int(selected_id), asset_title, asset_summary, asset_content)
                        update_task(
                            int(selected_id),
                            task["title"], task["description"], task["task_type"], task["context"],
                            task["suggested_model"], task["router_summary"], task["router_data_json"],
                            task["prompt_main"], task["prompt_system"], task["llm_output"], task["useful_extract"],
                            "ejecutado", task["tags"], task["uploads_json"]
                        )
                        st.success("Activo creado.")
                        st.rerun()
            with c3:
                task_md = Path(task["markdown_path"]) if task["markdown_path"] else None
                if task_md.exists():
                    st.download_button("Descargar ficha de tarea", data=task_md.read_text(encoding="utf-8"), file_name=task_md.name, mime="text/markdown", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)


def view_assets() -> None:
    st.subheader("Activos")
    rows = get_assets()
    if not rows:
        st.markdown('<div class="empty">Todavía no hay activos creados.</div>', unsafe_allow_html=True)
        return

    for row in rows:
        st.markdown(
            f"""
            <div class="soft-card">
                <div class="item-title">{row["title"]}</div>
                <div class="muted" style="margin-bottom:0.5rem;">Procede de: {row["task_title"]}</div>
                <div style="margin-bottom:0.7rem;"><strong>Resumen</strong><br>{row["summary"] or "Sin resumen."}</div>
                <div><strong>Contenido</strong><br>{row["content"][:600]}{"..." if len(row["content"]) > 600 else ""}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if row["markdown_path"] and Path(row["markdown_path"]).exists():
            content = Path(row["markdown_path"]).read_text(encoding="utf-8")
            st.download_button(
                f"Descargar activo #{row['id']}",
                data=content,
                file_name=Path(row["markdown_path"]).name,
                mime="text/markdown",
                key=f"asset_download_{row['id']}",
                use_container_width=True,
            )


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    init_db()
    inject_css()

    with st.sidebar:
        st.markdown("## Portable Work Router")
        page = st.radio("Navegación", ["Inbox", "Workspace", "Activos"], label_visibility="collapsed")
        st.caption("Local-first · portable by default")

    render_topbar()
    st.write("")

    if page == "Inbox":
        view_inbox()
    elif page == "Workspace":
        view_workspace()
    elif page == "Activos":
        view_assets()


if __name__ == "__main__":
    main()
