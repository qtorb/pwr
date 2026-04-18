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


# =========================
# Storage
# =========================
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


def generate_briefing(title: str, description: str, task_type: str, context: str) -> str:
    suggested_model = TASK_TYPES.get(task_type, "Modelo generalista")
    return f"""# Briefing de trabajo

## Tarea
{title}

## Tipo
{task_type}

## Modelo sugerido
{suggested_model}

## Qué necesito
{description}

## Contexto útil
{context.strip() or "Sin contexto adicional."}

## Instrucciones para el LLM
Actúa como un colaborador experto. Ayúdame con esta tarea de forma clara, estructurada y accionable.

Quiero:
1. Una respuesta útil para avanzar ya.
2. Buen criterio, no solo texto bonito.
3. Si detectas ambigüedad, propone la mejor interpretación operativa.
4. Evita relleno y repeticiones.
5. Prioriza claridad, estructura y utilidad práctica.

## Formato deseado
- Diagnóstico breve
- Propuesta principal
- Riesgos o límites
- Siguiente paso concreto
"""


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


# =========================
# CRUD
# =========================
def create_task(title: str, description: str, task_type: str, context: str, tags: str) -> int:
    created_at = now_iso()
    suggested_model = TASK_TYPES.get(task_type, "Modelo generalista")
    briefing = generate_briefing(title, description, task_type, context)

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


# =========================
# UI
# =========================
def inject_css() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background: #f5f7fb;
            color: #142033;
        }
        .block-container {
            max-width: 1460px;
            padding-top: 0.95rem;
            padding-bottom: 1.7rem;
            padding-left: 1.4rem;
            padding-right: 1.4rem;
        }
        h1, h2, h3, h4 {
            letter-spacing: -0.02em;
            color: #142033;
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #eef3fb 0%, #e8eff9 100%);
            border-right: 1px solid #d7deea;
        }
        [data-testid="stSidebar"] * {
            color: #142033 !important;
        }
        .shell-card {
            padding: 1rem 1.05rem;
            border: 1px solid #dbe3ef;
            background: #ffffff;
            border-radius: 18px;
            margin-bottom: 1rem;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
        }
        .top-card {
            padding: 1rem 1.15rem;
            border: 1px solid #dbe3ef;
            background: linear-gradient(180deg, #ffffff 0%, #fbfcfe 100%);
            border-radius: 18px;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
        }
        .muted {
            color: #61708a;
            font-size: 0.92rem;
        }
        .metric {
            padding: 0.9rem 1rem;
            border-radius: 16px;
            background: #ffffff;
            border: 1px solid #dbe3ef;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
            min-height: 86px;
        }
        .task-row {
            padding: 0.85rem 0.95rem;
            border: 1px solid #dbe3ef;
            background: #ffffff;
            border-radius: 16px;
            margin-bottom: 0.75rem;
            box-shadow: 0 1px 1px rgba(16, 24, 40, 0.03);
        }
        .task-title {
            font-weight: 700;
            font-size: 1.01rem;
            margin-bottom: 0.2rem;
            color: #142033;
        }
        .pill {
            display: inline-block;
            padding: 0.17rem 0.52rem;
            border-radius: 999px;
            background: #eef3fb;
            border: 1px solid #d7deea;
            color: #31405d;
            margin-right: 0.3rem;
            font-size: 0.74rem;
        }
        .section-chip {
            display: inline-block;
            padding: 0.18rem 0.56rem;
            border-radius: 999px;
            background: #edf4ff;
            color: #31527d;
            border: 1px solid #d8e6fb;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.01em;
            margin-bottom: 0.45rem;
        }
        .section-label {
            font-size: 1rem;
            font-weight: 700;
            color: #22324f;
            margin-top: 0.15rem;
            margin-bottom: 0.45rem;
        }
        .empty {
            padding: 2rem 1.2rem;
            border-radius: 18px;
            text-align: center;
            border: 1px dashed #c9d4e5;
            background: #ffffff;
            color: #61708a;
        }
        .soft-sep {
            height: 1px;
            background: #edf1f7;
            margin: 0.65rem 0 0.9rem 0;
        }
        div[data-baseweb="select"] > div,
        .stTextInput input,
        .stTextArea textarea {
            border-radius: 12px !important;
            border: 1px solid #cfd8e6 !important;
            background: #ffffff !important;
            color: #142033 !important;
            box-shadow: none !important;
        }
        .stTextArea textarea {
            line-height: 1.46 !important;
        }
        .stTextInput input:focus,
        .stTextArea textarea:focus {
            border-color: #97b4de !important;
            box-shadow: 0 0 0 1px #97b4de !important;
        }
        div.stButton > button,
        .stDownloadButton > button,
        div[data-testid="stFormSubmitButton"] > button {
            border-radius: 12px !important;
            border: 1px solid #cfd8e6 !important;
            background: #ffffff !important;
            color: #142033 !important;
            padding: 0.55rem 0.9rem !important;
            font-weight: 600 !important;
        }
        div.stButton > button:hover,
        .stDownloadButton > button:hover,
        div[data-testid="stFormSubmitButton"] > button:hover {
            border-color: #94a8c6 !important;
            background: #f8fbff !important;
        }
        .primary-cta {
            padding: 0.9rem 1rem;
            border: 1px solid #dce7f8;
            background: linear-gradient(180deg, #f7fbff 0%, #eef5ff 100%);
            border-radius: 16px;
            margin-bottom: 1rem;
        }
        .tiny {
            font-size: 0.82rem;
            color: #6d7c97;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_topbar() -> None:
    s = stats()
    left, right = st.columns([2.2, 1.25], gap="medium")
    with left:
        st.markdown(
            """
            <div class="top-card">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;flex-wrap:wrap;">
                    <div>
                        <h1 style="margin:0;">Portable Work Router</h1>
                        <div class="muted">Trabajo con LLMs más claro, más portable y menos caótico.</div>
                    </div>
                    <div class="tiny">v2 UX review</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="metric"><div class="muted">Tareas</div><div style="font-size:1.4rem;font-weight:700;">{s["tasks"]}</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric"><div class="muted">Assets</div><div style="font-size:1.4rem;font-weight:700;">{s["assets"]}</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric"><div class="muted">Activas</div><div style="font-size:1.4rem;font-weight:700;">{s["active"]}</div></div>', unsafe_allow_html=True)


def ensure_selected_task(rows: list[sqlite3.Row]) -> Optional[int]:
    if not rows:
        return None
    valid_ids = [int(r["id"]) for r in rows]
    selected = st.session_state.get("selected_task_id")
    if selected not in valid_ids:
        st.session_state["selected_task_id"] = valid_ids[0]
    return st.session_state["selected_task_id"]


def render_task_list(rows: list[sqlite3.Row], key_suffix: str) -> None:
    if not rows:
        st.markdown('<div class="empty">No hay tareas todavía.</div>', unsafe_allow_html=True)
        return

    for row in rows:
        selected = st.session_state.get("selected_task_id") == int(row["id"])
        border = "#97b4de" if selected else "#dbe3ef"
        bg = "#f8fbff" if selected else "#ffffff"
        st.markdown(
            f"""
            <div class="task-row" style="border-color:{border}; background:{bg};">
                <div class="task-title">{row["title"]}</div>
                <div class="muted" style="margin-bottom:0.42rem;">{row["description"][:96]}{"..." if len(row["description"]) > 96 else ""}</div>
                <span class="pill">{row["task_type"]}</span>
                <span class="pill">{row["status"]}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(f"Abrir #{row['id']}", key=f"open_{key_suffix}_{row['id']}", use_container_width=True):
            st.session_state["selected_task_id"] = int(row["id"])
            st.rerun()


def create_quick_task() -> None:
    st.markdown(
        """
        <div class="primary-cta">
            <div class="section-chip">INBOX</div>
            <div class="section-label">Crear nueva tarea</div>
            <div class="muted">Entrada rápida para capturar trabajo sin perder contexto.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    title = st.text_input("¿Qué quieres hacer?", placeholder="Ej.: Preparar briefing para nuevo onboarding")
    c1, c2 = st.columns([1, 1])
    with c1:
        task_type = st.selectbox("Tipo", list(TASK_TYPES.keys()), key="quick_type")
    with c2:
        tags = st.text_input("Tags", placeholder="pwr, ux, onboarding", key="quick_tags")
    description = st.text_area("Descripción", placeholder="Qué necesitas conseguir con esta tarea.", height=110)
    context = st.text_area("Contexto inicial", placeholder="Notas, restricciones, antecedentes o ideas previas.", height=150)

    if st.button("Crear tarea", use_container_width=True):
        if not title.strip() or not description.strip():
            st.error("Título y descripción son obligatorios.")
        else:
            task_id = create_task(title, description, task_type, context, tags)
            st.session_state["selected_task_id"] = task_id
            try:
                st.toast("Tarea creada")
            except Exception:
                st.success("Tarea creada")
            st.rerun()


def render_workspace_header(row: sqlite3.Row) -> None:
    st.markdown(
        f"""
        <div class="shell-card">
            <div class="section-chip">WORKSPACE</div>
            <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;flex-wrap:wrap;">
                <div>
                    <div class="task-title" style="font-size:1.1rem;">{row["title"]}</div>
                    <div class="muted">ID #{row["id"]} · Última actualización: {row["updated_at"]}</div>
                </div>
                <div>
                    <span class="pill">{row["task_type"]}</span>
                    <span class="pill">{row["status"]}</span>
                    <span class="pill">{row["suggested_model"]}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section(title: str, chip: str) -> None:
    st.markdown(
        f"""
        <div class="section-chip">{chip}</div>
        <div class="section-label">{title}</div>
        """,
        unsafe_allow_html=True,
    )


def view_inbox() -> None:
    create_quick_task()
    st.write("")
    section("Tareas recientes", "LISTA")
    search = st.text_input("Buscar tareas", placeholder="Título, descripción o tags", key="inbox_search")
    rows = get_tasks(search=search)
    render_task_list(rows, "inbox")


def view_workspace() -> None:
    rows = get_tasks()
    if not rows:
        st.markdown('<div class="empty">Crea primero una tarea en Inbox.</div>', unsafe_allow_html=True)
        return

    selected_id = ensure_selected_task(rows)
    if selected_id is None:
        return

    left, right = st.columns([0.95, 2.05], gap="large")

    with left:
        section("Navegación de tareas", "TASKS")
        search = st.text_input("Filtrar", placeholder="Buscar...", key="workspace_search")
        status_filter = st.selectbox(
            "Estado",
            ["", *STATUS_OPTIONS],
            index=0,
            format_func=lambda x: "Todos" if x == "" else x,
            key="workspace_status_filter",
        )
        filtered_rows = get_tasks(search=search, only_status=status_filter)
        if not filtered_rows:
            st.markdown('<div class="empty">Sin resultados.</div>', unsafe_allow_html=True)
        else:
            ensure_selected_task(filtered_rows)
            render_task_list(filtered_rows, "workspace")

    with right:
        row = get_task(int(st.session_state["selected_task_id"]))
        if row is None:
            st.warning("No se pudo cargar la tarea.")
            return

        render_workspace_header(row)

        title = st.text_input("Título", value=row["title"], key=f"title_{row['id']}")
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            task_type = st.selectbox(
                "Tipo",
                list(TASK_TYPES.keys()),
                index=list(TASK_TYPES.keys()).index(row["task_type"]) if row["task_type"] in TASK_TYPES else 0,
                key=f"type_{row['id']}",
            )
        with c2:
            status = st.selectbox(
                "Estado",
                STATUS_OPTIONS,
                index=STATUS_OPTIONS.index(row["status"]) if row["status"] in STATUS_OPTIONS else 0,
                key=f"status_{row['id']}",
            )
        with c3:
            suggested_model = st.text_input("Modelo sugerido", value=row["suggested_model"], key=f"model_{row['id']}")

        description = st.text_area("Descripción", value=row["description"], height=110, key=f"desc_{row['id']}")
        tags = st.text_input("Tags", value=row["tags"], key=f"tags_{row['id']}")

        st.markdown('<div class="soft-sep"></div>', unsafe_allow_html=True)
        top_left, top_right = st.columns([1.15, 0.85], gap="large")

        with top_left:
            section("Contexto", "INPUT")
            context = st.text_area(
                "Contexto",
                value=row["context"],
                height=250,
                label_visibility="collapsed",
                key=f"context_{row['id']}",
            )

            section("Briefing", "ROUTER")
            briefing = st.text_area(
                "Briefing",
                value=row["briefing"],
                height=300,
                label_visibility="collapsed",
                key=f"briefing_{row['id']}",
            )

            b1, b2, b3 = st.columns([1, 1, 1])
            with b1:
                if st.button("Guardar", use_container_width=True, key=f"save_{row['id']}"):
                    update_task(
                        task_id=int(row["id"]),
                        title=title,
                        description=description,
                        task_type=task_type,
                        context=context,
                        suggested_model=suggested_model,
                        briefing=briefing,
                        llm_output=st.session_state.get(f"llm_{row['id']}", row["llm_output"]),
                        useful_extract=st.session_state.get(f"extract_{row['id']}", row["useful_extract"]),
                        status=status,
                        tags=tags,
                    )
                    try:
                        st.toast("Guardado")
                    except Exception:
                        st.success("Guardado")
                    st.rerun()
            with b2:
                if st.button("Regenerar", use_container_width=True, key=f"regen_{row['id']}"):
                    regenerated = generate_briefing(title, description, task_type, context)
                    new_model = TASK_TYPES.get(task_type, "Modelo generalista")
                    update_task(
                        task_id=int(row["id"]),
                        title=title,
                        description=description,
                        task_type=task_type,
                        context=context,
                        suggested_model=new_model,
                        briefing=regenerated,
                        llm_output=st.session_state.get(f"llm_{row['id']}", row["llm_output"]),
                        useful_extract=st.session_state.get(f"extract_{row['id']}", row["useful_extract"]),
                        status="brief_ready",
                        tags=tags,
                    )
                    try:
                        st.toast("Briefing regenerado")
                    except Exception:
                        st.success("Briefing regenerado")
                    st.rerun()
            with b3:
                st.download_button(
                    "Descargar briefing",
                    data=briefing,
                    file_name=f"briefing-task-{row['id']}.md",
                    mime="text/markdown",
                    use_container_width=True,
                    key=f"brief_dl_{row['id']}",
                )

        with top_right:
            st.markdown(
                f"""
                <div class="shell-card">
                    <div class="section-chip">SUMMARY</div>
                    <div class="section-label">Ficha rápida</div>
                    <div class="muted" style="margin-bottom:0.5rem;">Tipo: {task_type}</div>
                    <div class="muted" style="margin-bottom:0.5rem;">Modelo: {suggested_model}</div>
                    <div class="muted" style="margin-bottom:0.5rem;">Estado: {status}</div>
                    <div class="muted">Tags: {tags or "Sin tags"}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                """
                <div class="shell-card">
                    <div class="section-chip">GUIDE</div>
                    <div class="section-label">Uso recomendado</div>
                    <div class="tiny">1. Ajusta contexto.</div>
                    <div class="tiny">2. Regenera briefing si cambia la intención.</div>
                    <div class="tiny">3. Pega el output del LLM.</div>
                    <div class="tiny">4. Extrae lo reusable.</div>
                    <div class="tiny">5. Convierte en asset.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            task_md = Path(row["markdown_path"]) if row["markdown_path"] else None
            if task_md.exists():
                st.download_button(
                    "Descargar tarea completa",
                    data=task_md.read_text(encoding="utf-8"),
                    file_name=task_md.name,
                    mime="text/markdown",
                    use_container_width=True,
                    key=f"task_dl_{row['id']}",
                )

        st.markdown('<div class="soft-sep"></div>', unsafe_allow_html=True)
        bottom_left, bottom_right = st.columns([1.15, 0.85], gap="large")

        with bottom_left:
            section("Output LLM", "OUTPUT")
            llm_output = st.text_area(
                "Output del LLM",
                value=row["llm_output"],
                height=260,
                label_visibility="collapsed",
                key=f"llm_{row['id']}",
            )

            section("Extracto útil", "ASSET")
            useful_extract = st.text_area(
                "Extracto útil",
                value=row["useful_extract"],
                height=220,
                label_visibility="collapsed",
                key=f"extract_{row['id']}",
            )

        with bottom_right:
            st.markdown(
                """
                <div class="shell-card">
                    <div class="section-chip">FINALIZE</div>
                    <div class="section-label">Convertir en asset</div>
                    <div class="muted">Toma el extracto útil o, si no existe, el output completo.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Crear asset", use_container_width=True, key=f"asset_{row['id']}"):
                content = useful_extract.strip() or llm_output.strip()
                if not content:
                    st.error("No hay contenido para convertir en asset.")
                else:
                    asset_id = create_asset(
                        task_id=int(row["id"]),
                        title=f"Asset · {title}",
                        summary=description,
                        content=content,
                    )
                    update_task(
                        task_id=int(row["id"]),
                        title=title,
                        description=description,
                        task_type=task_type,
                        context=context,
                        suggested_model=suggested_model,
                        briefing=briefing,
                        llm_output=llm_output,
                        useful_extract=useful_extract,
                        status="executed",
                        tags=tags,
                    )
                    st.session_state["last_asset_id"] = asset_id
                    try:
                        st.toast("Asset creado")
                    except Exception:
                        st.success("Asset creado")
                    st.rerun()


def view_assets() -> None:
    rows = get_assets()
    section("Assets", "LIBRARY")
    if not rows:
        st.markdown('<div class="empty">Todavía no hay assets creados.</div>', unsafe_allow_html=True)
        return

    for row in rows:
        st.markdown(
            f"""
            <div class="shell-card">
                <div class="task-title">{row["title"]}</div>
                <div class="muted" style="margin-bottom:0.55rem;">Desde: {row["task_title"]}</div>
                <div style="margin-bottom:0.65rem;"><strong>Resumen</strong><br>{row["summary"] or "Sin resumen."}</div>
                <div><strong>Contenido</strong><br>{row["content"][:700]}{"..." if len(row["content"]) > 700 else ""}</div>
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
                use_container_width=True,
                key=f"asset_dl_{row['id']}",
            )


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    init_db()
    inject_css()

    with st.sidebar:
        st.markdown("## Portable Work Router")
        page = st.radio("Navegación", ["Inbox", "Workspace", "Assets"], label_visibility="collapsed")
        st.caption("Local-first · portable by default")

    render_topbar()
    st.write("")

    if page == "Inbox":
        view_inbox()
    elif page == "Workspace":
        view_workspace()
    else:
        view_assets()


if __name__ == "__main__":
    main()
