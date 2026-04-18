import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional

import streamlit as st

APP_TITLE = "Portable Work Router"
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "pwr_data"
TASKS_DIR = DATA_DIR / "tasks"
ASSETS_DIR = DATA_DIR / "assets"
DB_PATH = DATA_DIR / "pwr.db"

TASK_TYPES = {
    "Pensar": "ChatGPT o Claude",
    "Escribir": "Claude",
    "Programar": "Codex",
    "Revisar": "Claude",
    "Decidir": "ChatGPT",
}
STATUS_OPTIONS = ["draft", "brief_ready", "executed", "archived"]
STEP_ORDER = ["Tarea", "Router", "Briefing", "Output", "Asset"]


def ensure_dirs() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    TASKS_DIR.mkdir(exist_ok=True)
    ASSETS_DIR.mkdir(exist_ok=True)


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
                briefing TEXT DEFAULT '',
                llm_output TEXT DEFAULT '',
                useful_extract TEXT DEFAULT '',
                status TEXT DEFAULT 'draft',
                tags TEXT DEFAULT '',
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


def write_task_markdown(task: sqlite3.Row | dict) -> str:
    path = task_markdown_path(int(task["id"]), str(task["title"]))
    content = f"""# {task["title"]}

- ID: {task["id"]}
- Tipo: {task["task_type"]}
- Modelo sugerido: {task["suggested_model"]}
- Estado: {task["status"]}
- Tags: {task["tags"]}
- Creado: {task["created_at"]}
- Actualizado: {task["updated_at"]}

## Descripción
{task["description"]}

## Contexto
{task["context"]}

## Briefing
{task["briefing"]}

## Output LLM
{task["llm_output"]}

## Extracto útil
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


def score_model(task_type: str, title: str, description: str, context: str):
    text = f"{title} {description} {context}".lower()
    scores = {
        "Claude": 0,
        "ChatGPT": 0,
        "Codex": 0,
        "Gemini": 0,
    }
    reasons = {
        "Claude": [],
        "ChatGPT": [],
        "Codex": [],
        "Gemini": [],
    }

    if task_type == "Escribir":
        scores["Claude"] += 4
        reasons["Claude"].append("la tarea es principalmente de escritura estructurada")
        scores["ChatGPT"] += 2
        reasons["ChatGPT"].append("puede ayudar a explorar variantes rápidamente")

    if task_type == "Pensar":
        scores["ChatGPT"] += 4
        reasons["ChatGPT"].append("la tarea parece de exploración o pensamiento general")
        scores["Claude"] += 3
        reasons["Claude"].append("puede aportar estructura y profundidad")

    if task_type == "Programar":
        scores["Codex"] += 6
        reasons["Codex"].append("la tarea es de programación")
        scores["ChatGPT"] += 1
        reasons["ChatGPT"].append("sirve como apoyo de contraste rápido")

    if task_type == "Revisar":
        scores["Claude"] += 4
        reasons["Claude"].append("la revisión suele beneficiarse de respuestas cuidadas")
        scores["ChatGPT"] += 2
        reasons["ChatGPT"].append("puede resumir o contrastar con rapidez")

    if task_type == "Decidir":
        scores["ChatGPT"] += 4
        reasons["ChatGPT"].append("la tarea parece de decisión o framing")
        scores["Claude"] += 2
        reasons["Claude"].append("puede ayudar a ordenar trade-offs")

    long_context = len(context.strip()) > 400
    if long_context:
        scores["Claude"] += 2
        reasons["Claude"].append("hay bastante contexto y suele manejar bien entradas largas")

    if any(k in text for k in ["estrateg", "posicion", "marca", "narrativa", "mensaje", "editorial"]):
        scores["Claude"] += 2
        reasons["Claude"].append("hay una capa estratégica/editorial relevante")

    if any(k in text for k in ["python", "script", "bug", "api", "backend", "frontend", "sql", "streamlit"]):
        scores["Codex"] += 3
        reasons["Codex"].append("aparecen señales de trabajo técnico o de código")

    if any(k in text for k in ["comparar", "alternativas", "opciones", "brainstorm", "ideas"]):
        scores["ChatGPT"] += 2
        reasons["ChatGPT"].append("conviene explorar opciones con agilidad")
        scores["Gemini"] += 1
        reasons["Gemini"].append("puede servir como segunda opinión")

    if any(k in text for k in ["contraste", "segunda opinión", "segunda opinion", "validar", "verificar"]):
        scores["Gemini"] += 3
        reasons["Gemini"].append("encaja como modelo de contraste")
        scores["ChatGPT"] += 1
        reasons["ChatGPT"].append("también puede servir como contraste")

    ranking = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    recommended = ranking[0][0]
    alternatives = [name for name, _ in ranking[1:3]]

    primary_reasons = reasons[recommended][:3]
    if not primary_reasons:
        primary_reasons = ["encaja razonablemente bien con el tipo de tarea"]

    explanation = {
        "recommended_model": recommended,
        "alternatives": alternatives,
        "reasons": primary_reasons,
        "scores": scores,
    }
    return explanation


def generate_router_summary(task_type: str, title: str, description: str, context: str) -> str:
    r = score_model(task_type, title, description, context)
    lines = [
        f"Modelo recomendado: {r['recommended_model']}",
        "",
        "Motivos principales:",
    ]
    lines.extend([f"- {reason}" for reason in r["reasons"]])
    if r["alternatives"]:
        lines.append("")
        lines.append("Alternativas útiles:")
        lines.extend([f"- {alt}" for alt in r["alternatives"]])
    return "\n".join(lines)


def generate_briefing(title: str, description: str, task_type: str, context: str, suggested_model: str) -> str:
    return f"""# Briefing de trabajo

## Tarea
{title}

## Tipo
{task_type}

## Modelo recomendado
{suggested_model}

## Qué necesito
{description}

## Contexto útil
{context.strip() or "Sin contexto adicional."}

## Instrucciones para el modelo
Actúa como un colaborador experto. Ayúdame con esta tarea de forma clara, estructurada y accionable.

Quiero:
1. Una respuesta útil para avanzar ya.
2. Buen criterio, no solo texto bonito.
3. Si detectas ambigüedad, propón la mejor interpretación operativa.
4. Evita relleno y repeticiones.
5. Prioriza claridad, estructura y utilidad práctica.

## Formato deseado
- Diagnóstico breve
- Propuesta principal
- Riesgos o límites
- Siguiente paso concreto
"""


def create_task(title: str, description: str, task_type: str, context: str, tags: str) -> int:
    created_at = now_iso()
    router = score_model(task_type, title, description, context)
    suggested_model = router["recommended_model"]
    briefing = generate_briefing(title, description, task_type, context, suggested_model)
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO tasks (
                title, description, task_type, context, suggested_model,
                briefing, status, tags, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                title.strip(),
                description.strip(),
                task_type,
                context.strip(),
                suggested_model,
                briefing,
                "brief_ready",
                tags.strip(),
                created_at,
                created_at,
            ),
        )
        task_id = int(cur.lastrowid)
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        md_path = write_task_markdown(row)
        conn.execute(
            "UPDATE tasks SET markdown_path = ?, updated_at = ? WHERE id = ?",
            (md_path, now_iso(), task_id),
        )
    return task_id


def update_task(
    task_id: int,
    title: str,
    description: str,
    task_type: str,
    context: str,
    suggested_model: str,
    briefing: str,
    llm_output: str,
    useful_extract: str,
    status: str,
    tags: str,
) -> None:
    updated_at = now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE tasks
            SET title = ?, description = ?, task_type = ?, context = ?, suggested_model = ?,
                briefing = ?, llm_output = ?, useful_extract = ?, status = ?, tags = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                title.strip(),
                description.strip(),
                task_type,
                context.strip(),
                suggested_model.strip(),
                briefing,
                llm_output,
                useful_extract,
                status,
                tags.strip(),
                updated_at,
                task_id,
            ),
        )
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        md_path = write_task_markdown(row)
        conn.execute(
            "UPDATE tasks SET markdown_path = ?, updated_at = ? WHERE id = ?",
            (md_path, now_iso(), task_id),
        )


def get_tasks(search: str = "", only_status: str = "") -> list[sqlite3.Row]:
    query = "SELECT * FROM tasks"
    clauses = []
    params: list[str] = []

    if search.strip():
        clauses.append("(title LIKE ? OR description LIKE ? OR tags LIKE ?)")
        pattern = f"%{search.strip()}%"
        params += [pattern, pattern, pattern]

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


def get_assets() -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT a.*, t.title AS task_title
            FROM assets a
            JOIN tasks t ON a.task_id = t.id
            ORDER BY a.created_at DESC, a.id DESC
            """
        ).fetchall()


def stats() -> dict[str, int]:
    with get_conn() as conn:
        task_count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        asset_count = conn.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
        active_count = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE status IN ('brief_ready', 'executed')"
        ).fetchone()[0]
    return {"tasks": task_count, "assets": asset_count, "active": active_count}


def inject_css() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background: #f5f7fb;
            color: #162033;
        }
        .block-container {
            max-width: 1440px;
            padding-top: 1.05rem;
            padding-bottom: 1.8rem;
            padding-left: 1.5rem;
            padding-right: 1.5rem;
        }
        h1, h2, h3 {
            letter-spacing: -0.02em;
            color: #162033;
        }
        [data-testid="stSidebar"] {
            background: #eef3fb;
            border-right: 1px solid #d7deea;
        }
        [data-testid="stSidebar"] * {
            color: #162033 !important;
        }
        .soft-card, .panel-card {
            padding: 1rem 1.1rem;
            border: 1px solid #dbe3ef;
            background: #ffffff;
            border-radius: 18px;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
        }
        .soft-card { margin-bottom: 1rem; }
        .muted {
            color: #5f6f89;
            font-size: 0.92rem;
        }
        .metric {
            padding: 0.9rem 1rem;
            border-radius: 16px;
            background: #ffffff;
            border: 1px solid #dbe3ef;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
        }
        .item-title {
            font-weight: 700;
            font-size: 1.02rem;
            margin-bottom: 0.2rem;
            color: #162033;
        }
        .pill {
            display: inline-block;
            padding: 0.18rem 0.55rem;
            border-radius: 999px;
            background: #eef3fb;
            border: 1px solid #d7deea;
            color: #33415c;
            margin-right: 0.35rem;
            font-size: 0.76rem;
        }
        .task-row {
            padding: 0.85rem 0.95rem;
            border: 1px solid #dbe3ef;
            background: #ffffff;
            border-radius: 16px;
            margin-bottom: 0.75rem;
        }
        .task-row.selected {
            border: 2px solid #6b8ac9;
            box-shadow: 0 0 0 3px rgba(107,138,201,0.10);
        }
        .empty {
            padding: 2rem 1.2rem;
            border-radius: 18px;
            text-align: center;
            border: 1px dashed #c9d4e5;
            background: #ffffff;
            color: #5f6f89;
        }
        .stepper {
            display: flex;
            gap: 0.55rem;
            flex-wrap: wrap;
            margin-bottom: 1rem;
        }
        .step {
            padding: 0.55rem 0.8rem;
            border-radius: 999px;
            border: 1px solid #d7deea;
            background: #ffffff;
            color: #5f6f89;
            font-size: 0.85rem;
            font-weight: 600;
        }
        .step.active {
            background: #162033;
            color: #ffffff;
            border-color: #162033;
        }
        .step.done {
            background: #eef6ef;
            color: #2f6f44;
            border-color: #b9d8c2;
        }
        .router-card {
            padding: 1.15rem 1.2rem;
            border-radius: 20px;
            background: linear-gradient(135deg, #18253b 0%, #243a5d 100%);
            color: #ffffff;
            border: 1px solid #223b63;
            box-shadow: 0 10px 24px rgba(27, 43, 70, 0.18);
        }
        .router-card * {
            color: #ffffff !important;
        }
        .router-badge {
            display: inline-block;
            padding: 0.22rem 0.6rem;
            border-radius: 999px;
            background: rgba(255,255,255,0.12);
            border: 1px solid rgba(255,255,255,0.18);
            margin-right: 0.35rem;
            font-size: 0.78rem;
        }
        .section-title {
            font-size: 0.95rem;
            font-weight: 700;
            color: #33415c;
            margin-top: 0.3rem;
            margin-bottom: 0.35rem;
        }
        div[data-baseweb="select"] > div,
        .stTextInput input,
        .stTextArea textarea {
            border-radius: 12px !important;
            border: 1px solid #cfd8e6 !important;
            background: #ffffff !important;
            color: #162033 !important;
        }
        .stTextArea textarea {
            line-height: 1.45 !important;
        }
        div.stButton > button,
        .stDownloadButton > button,
        div[data-testid="stFormSubmitButton"] > button {
            border-radius: 12px !important;
            border: 1px solid #cfd8e6 !important;
            background: #ffffff !important;
            color: #162033 !important;
            padding: 0.55rem 0.9rem !important;
            font-weight: 600 !important;
        }
        div.stButton > button:hover,
        .stDownloadButton > button:hover,
        div[data-testid="stFormSubmitButton"] > button:hover {
            border-color: #94a8c6 !important;
            background: #f8fbff !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_topbar() -> None:
    s = stats()
    c1, c2 = st.columns([2.1, 1.5])
    with c1:
        st.markdown(
            """
            <div class="soft-card">
                <h1 style="margin:0;">Portable Work Router</h1>
                <div class="muted">Secuencia operativa visible. Router de LLM en el centro del valor.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        mc1, mc2, mc3 = st.columns(3)
        mc1.markdown(f'<div class="metric"><div class="muted">Tareas</div><div style="font-size:1.42rem;font-weight:700;">{s["tasks"]}</div></div>', unsafe_allow_html=True)
        mc2.markdown(f'<div class="metric"><div class="muted">Assets</div><div style="font-size:1.42rem;font-weight:700;">{s["assets"]}</div></div>', unsafe_allow_html=True)
        mc3.markdown(f'<div class="metric"><div class="muted">Activas</div><div style="font-size:1.42rem;font-weight:700;">{s["active"]}</div></div>', unsafe_allow_html=True)


def render_stepper(current_step: str) -> None:
    statuses = []
    current_index = STEP_ORDER.index(current_step)
    for i, step in enumerate(STEP_ORDER):
        cls = "step"
        if i < current_index:
            cls += " done"
        elif i == current_index:
            cls += " active"
        statuses.append(f'<div class="{cls}">{i+1}. {step}</div>')
    st.markdown('<div class="stepper">' + "".join(statuses) + '</div>', unsafe_allow_html=True)


def ensure_selected_task(rows: list[sqlite3.Row]) -> Optional[int]:
    if not rows:
        return None
    selected = st.session_state.get("selected_task_id")
    valid_ids = [int(r["id"]) for r in rows]
    if selected not in valid_ids:
        st.session_state["selected_task_id"] = valid_ids[0]
    return st.session_state["selected_task_id"]


def create_quick_task_block() -> None:
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.subheader("Entrada rápida")
    render_stepper("Tarea")
    quick_title = st.text_input("¿Qué quieres hacer?", placeholder="Ej.: Preparar briefing para rediseño onboarding")
    c1, c2 = st.columns([1, 1])
    with c1:
        quick_type = st.selectbox("Tipo", list(TASK_TYPES.keys()), key="quick_type")
    with c2:
        quick_tags = st.text_input("Tags", placeholder="pwr, ux, onboarding", key="quick_tags")
    quick_desc = st.text_area("Descripción breve", placeholder="Qué necesitas conseguir con esta tarea.", height=110)
    quick_context = st.text_area("Contexto inicial", placeholder="Notas, restricciones, antecedentes.", height=150)

    if st.button("Crear tarea", use_container_width=True):
        if not quick_title.strip() or not quick_desc.strip():
            st.error("Título y descripción son obligatorios.")
        else:
            task_id = create_task(quick_title, quick_desc, quick_type, quick_context, quick_tags)
            st.session_state["selected_task_id"] = task_id
            st.session_state[f"step_{task_id}"] = "Router"
            try:
                st.toast("Tarea creada")
            except Exception:
                st.success("Tarea creada")
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


def render_task_list(rows: list[sqlite3.Row], selected_id: Optional[int]) -> None:
    if not rows:
        st.markdown('<div class="empty">Todavía no hay tareas.</div>', unsafe_allow_html=True)
        return
    for row in rows:
        selected_class = " selected" if int(row["id"]) == selected_id else ""
        st.markdown(
            f"""
            <div class="task-row{selected_class}">
                <div class="item-title">{row["title"]}</div>
                <div class="muted" style="margin-bottom:0.45rem;">{row["description"][:95]}{"..." if len(row["description"]) > 95 else ""}</div>
                <span class="pill">{row["task_type"]}</span>
                <span class="pill">{row["status"]}</span>
                <span class="pill">{row["suggested_model"] or "Sin router"}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(f"Seleccionar #{row['id']}", key=f"task_pick_{row['id']}", use_container_width=True):
            st.session_state["selected_task_id"] = int(row["id"])
            st.rerun()


def view_inbox() -> None:
    create_quick_task_block()
    st.write("")
    st.subheader("Tareas recientes")
    search = st.text_input("Buscar tareas", placeholder="Título, descripción o tags", key="inbox_search")
    rows = get_tasks(search=search)
    selected_id = st.session_state.get("selected_task_id")
    render_task_list(rows, selected_id)


def view_workspace() -> None:
    rows = get_tasks()
    if not rows:
        st.markdown('<div class="empty">Crea primero una tarea en Inbox para empezar a trabajar.</div>', unsafe_allow_html=True)
        return

    selected_id = ensure_selected_task(rows)
    if selected_id is None:
        return

    task = get_task(int(selected_id))
    if task is None:
        st.warning("No se pudo cargar la tarea.")
        return

    current_step = st.session_state.get(f"step_{selected_id}", "Tarea")

    left, right = st.columns([0.9, 2.1], gap="large")

    with left:
        st.subheader("Tareas")
        search = st.text_input("Filtrar", placeholder="Buscar...", key="workspace_search")
        status_filter = st.selectbox(
            "Estado",
            ["", *STATUS_OPTIONS],
            index=0,
            format_func=lambda x: "Todos" if x == "" else x,
            key="workspace_status_filter",
        )
        filtered_rows = get_tasks(search=search, only_status=status_filter)
        rows_to_show = filtered_rows or rows
        render_task_list(rows_to_show, selected_id)

    with right:
        st.subheader("Workspace")
        render_stepper(current_step)

        title_key = f"title_{selected_id}"
        type_key = f"type_{selected_id}"
        desc_key = f"desc_{selected_id}"
        ctx_key = f"context_{selected_id}"
        model_key = f"model_{selected_id}"
        tags_key = f"tags_{selected_id}"
        briefing_key = f"briefing_{selected_id}"
        llm_key = f"llm_{selected_id}"
        extract_key = f"extract_{selected_id}"
        status_key = f"status_{selected_id}"

        defaults = {
            title_key: task["title"],
            type_key: task["task_type"],
            desc_key: task["description"],
            ctx_key: task["context"],
            model_key: task["suggested_model"],
            tags_key: task["tags"],
            briefing_key: task["briefing"],
            llm_key: task["llm_output"],
            extract_key: task["useful_extract"],
            status_key: task["status"],
        }
        for k, v in defaults.items():
            if k not in st.session_state:
                st.session_state[k] = v

        title = st.session_state[title_key]
        task_type = st.session_state[type_key]
        description = st.session_state[desc_key]
        context = st.session_state[ctx_key]
        suggested_model = st.session_state[model_key]
        tags = st.session_state[tags_key]
        briefing = st.session_state[briefing_key]
        llm_output = st.session_state[llm_key]
        useful_extract = st.session_state[extract_key]
        status = st.session_state[status_key]

        if current_step == "Tarea":
            st.markdown('<div class="panel-card">', unsafe_allow_html=True)
            st.text_input("Título", key=title_key)
            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                st.selectbox("Tipo", list(TASK_TYPES.keys()), key=type_key)
            with c2:
                st.selectbox("Estado", STATUS_OPTIONS, key=status_key)
            with c3:
                st.text_input("Tags", key=tags_key)
            st.text_area("Descripción", height=120, key=desc_key)
            st.text_area("Contexto", height=260, key=ctx_key)
            b1, b2 = st.columns([1, 1])
            with b1:
                if st.button("Guardar tarea", use_container_width=True):
                    router = score_model(st.session_state[type_key], st.session_state[title_key], st.session_state[desc_key], st.session_state[ctx_key])
                    model = router["recommended_model"]
                    new_briefing = generate_briefing(
                        st.session_state[title_key],
                        st.session_state[desc_key],
                        st.session_state[type_key],
                        st.session_state[ctx_key],
                        model,
                    )
                    st.session_state[model_key] = model
                    st.session_state[briefing_key] = new_briefing
                    update_task(
                        int(selected_id),
                        st.session_state[title_key],
                        st.session_state[desc_key],
                        st.session_state[type_key],
                        st.session_state[ctx_key],
                        model,
                        new_briefing,
                        st.session_state[llm_key],
                        st.session_state[extract_key],
                        st.session_state[status_key],
                        st.session_state[tags_key],
                    )
                    try:
                        st.toast("Tarea guardada")
                    except Exception:
                        st.success("Tarea guardada")
                    st.rerun()
            with b2:
                if st.button("Siguiente: Router", use_container_width=True):
                    st.session_state[f"step_{selected_id}"] = "Router"
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        elif current_step == "Router":
            router = score_model(
                st.session_state[ type_key ],
                st.session_state[ title_key ],
                st.session_state[ desc_key ],
                st.session_state[ ctx_key ],
            )
            st.markdown(
                f"""
                <div class="router-card">
                    <div class="muted" style="color:rgba(255,255,255,0.75) !important;">Recomendación inteligente</div>
                    <div style="font-size:2rem;font-weight:800;margin-top:0.15rem;">{router["recommended_model"]}</div>
                    <div style="margin-top:0.75rem;margin-bottom:0.75rem;">
                        {"".join([f'<span class="router-badge">{alt}</span>' for alt in router["alternatives"]])}
                    </div>
                    <div style="font-weight:700;margin-bottom:0.35rem;">Por qué encaja</div>
                    <ul style="margin-top:0.2rem;">
                        {"".join([f"<li>{reason}</li>" for reason in router["reasons"]])}
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.write("")
            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                if st.button("Volver a tarea", use_container_width=True):
                    st.session_state[f"step_{selected_id}"] = "Tarea"
                    st.rerun()
            with c2:
                if st.button("Aceptar recomendación", use_container_width=True):
                    model = router["recommended_model"]
                    st.session_state[model_key] = model
                    st.session_state[briefing_key] = generate_briefing(
                        st.session_state[title_key],
                        st.session_state[desc_key],
                        st.session_state[type_key],
                        st.session_state[ctx_key],
                        model,
                    )
                    update_task(
                        int(selected_id),
                        st.session_state[title_key],
                        st.session_state[desc_key],
                        st.session_state[type_key],
                        st.session_state[ctx_key],
                        model,
                        st.session_state[briefing_key],
                        st.session_state[llm_key],
                        st.session_state[extract_key],
                        "brief_ready",
                        st.session_state[tags_key],
                    )
                    st.session_state[f"step_{selected_id}"] = "Briefing"
                    st.rerun()
            with c3:
                if st.button("Recalcular router", use_container_width=True):
                    st.rerun()

        elif current_step == "Briefing":
            st.markdown('<div class="panel-card">', unsafe_allow_html=True)
            c1, c2 = st.columns([1.2, 0.8])
            with c1:
                st.markdown("### Briefing listo para usar")
                st.text_area("Briefing", height=360, key=briefing_key, label_visibility="collapsed")
            with c2:
                st.markdown("### Router")
                st.markdown(
                    f"""
                    <div class="soft-card" style="margin-bottom:0;">
                        <div class="muted">Modelo recomendado</div>
                        <div style="font-size:1.5rem;font-weight:800;margin-top:0.15rem;">{st.session_state[model_key] or "—"}</div>
                        <div class="muted" style="margin-top:0.8rem;">Este es el momento clave del producto: decidir bien antes de ejecutar.</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                if st.button("Volver al router", use_container_width=True):
                    st.session_state[f"step_{selected_id}"] = "Router"
                    st.rerun()
            with c2:
                st.download_button(
                    "Descargar briefing",
                    data=st.session_state[briefing_key],
                    file_name=f"briefing-task-{selected_id}.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
            with c3:
                if st.button("Ya tengo el resultado", use_container_width=True):
                    update_task(
                        int(selected_id),
                        st.session_state[title_key],
                        st.session_state[desc_key],
                        st.session_state[type_key],
                        st.session_state[ctx_key],
                        st.session_state[model_key],
                        st.session_state[briefing_key],
                        st.session_state[llm_key],
                        st.session_state[extract_key],
                        "brief_ready",
                        st.session_state[tags_key],
                    )
                    st.session_state[f"step_{selected_id}"] = "Output"
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        elif current_step == "Output":
            st.markdown('<div class="panel-card">', unsafe_allow_html=True)
            st.markdown("### Pega aquí la respuesta del modelo")
            st.text_area("Output del LLM", height=300, key=llm_key, label_visibility="collapsed")
            st.markdown("### Qué quieres conservar")
            st.text_area("Extracto útil", height=220, key=extract_key, label_visibility="collapsed")
            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                if st.button("Volver al briefing", use_container_width=True):
                    st.session_state[f"step_{selected_id}"] = "Briefing"
                    st.rerun()
            with c2:
                if st.button("Guardar output", use_container_width=True):
                    update_task(
                        int(selected_id),
                        st.session_state[title_key],
                        st.session_state[desc_key],
                        st.session_state[type_key],
                        st.session_state[ctx_key],
                        st.session_state[model_key],
                        st.session_state[briefing_key],
                        st.session_state[llm_key],
                        st.session_state[extract_key],
                        "executed",
                        st.session_state[tags_key],
                    )
                    try:
                        st.toast("Output guardado")
                    except Exception:
                        st.success("Output guardado")
                    st.rerun()
            with c3:
                if st.button("Siguiente: Asset", use_container_width=True):
                    st.session_state[f"step_{selected_id}"] = "Asset"
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        elif current_step == "Asset":
            st.markdown('<div class="panel-card">', unsafe_allow_html=True)
            st.markdown("### Convertir en activo portable")
            content = st.session_state[extract_key].strip() or st.session_state[llm_key].strip()
            st.text_input("Título del asset", value=f"Asset · {st.session_state[title_key]}", key=f"asset_title_{selected_id}")
            st.text_area("Resumen", value=st.session_state[desc_key], height=90, key=f"asset_summary_{selected_id}")
            st.text_area("Contenido final", value=content, height=260, key=f"asset_content_{selected_id}")
            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                if st.button("Volver al output", use_container_width=True):
                    st.session_state[f"step_{selected_id}"] = "Output"
                    st.rerun()
            with c2:
                if st.button("Crear asset", use_container_width=True):
                    final_content = st.session_state[f"asset_content_{selected_id}"].strip()
                    if not final_content:
                        st.error("No hay contenido para convertir en asset.")
                    else:
                        asset_id = create_asset(
                            int(selected_id),
                            st.session_state[f"asset_title_{selected_id}"],
                            st.session_state[f"asset_summary_{selected_id}"],
                            final_content,
                        )
                        update_task(
                            int(selected_id),
                            st.session_state[title_key],
                            st.session_state[desc_key],
                            st.session_state[type_key],
                            st.session_state[ctx_key],
                            st.session_state[model_key],
                            st.session_state[briefing_key],
                            st.session_state[llm_key],
                            st.session_state[extract_key],
                            "executed",
                            st.session_state[tags_key],
                        )
                        st.session_state["last_asset_id"] = asset_id
                        try:
                            st.toast("Asset creado")
                        except Exception:
                            st.success("Asset creado")
                        st.rerun()
            with c3:
                task_md = Path(task["markdown_path"]) if task["markdown_path"] else None
                if task_md.exists():
                    st.download_button(
                        "Descargar tarea",
                        data=task_md.read_text(encoding="utf-8"),
                        file_name=task_md.name,
                        mime="text/markdown",
                        use_container_width=True,
                    )
            st.markdown('</div>', unsafe_allow_html=True)


def view_assets() -> None:
    st.subheader("Assets")
    rows = get_assets()
    if not rows:
        st.markdown('<div class="empty">Todavía no hay assets creados.</div>', unsafe_allow_html=True)
        return
    for row in rows:
        st.markdown(
            f"""
            <div class="soft-card">
                <div class="item-title">{row["title"]}</div>
                <div class="muted" style="margin-bottom:0.5rem;">Desde: {row["task_title"]}</div>
                <div style="margin-bottom:0.7rem;"><strong>Resumen</strong><br>{row["summary"] or "Sin resumen."}</div>
                <div><strong>Contenido</strong><br>{row["content"][:600]}{"..." if len(row["content"]) > 600 else ""}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if row["markdown_path"] and Path(row["markdown_path"]).exists():
            content = Path(row["markdown_path"]).read_text(encoding="utf-8")
            st.download_button(
                f"Descargar asset #{row['id']}",
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
        page = st.radio(
            "Navegación",
            ["Inbox", "Workspace", "Assets"],
            label_visibility="collapsed",
        )
        st.caption("Local-first · portable by default")

    render_topbar()
    st.write("")

    if page == "Inbox":
        view_inbox()
    elif page == "Workspace":
        view_workspace()
    elif page == "Assets":
        view_assets()


if __name__ == "__main__":
    main()
