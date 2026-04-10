import os
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional

import streamlit as st

# =========================
# Config
# =========================
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
# Storage helpers
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

## Formato deseado de respuesta
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
        conn.execute(
            "UPDATE assets SET markdown_path = ? WHERE id = ?",
            (md_path, asset_id),
        )
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
        ready_count = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE status IN ('brief_ready', 'executed')"
        ).fetchone()[0]
    return {"tasks": task_count, "assets": asset_count, "active": ready_count}


# =========================
# UI helpers
# =========================
def inject_css() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background: #0b1020;
            color: #e8edf7;
        }
        .block-container {
            max-width: 1400px;
            padding-top: 1.4rem;
            padding-bottom: 2rem;
            padding-left: 2rem;
            padding-right: 2rem;
        }
        h1, h2, h3 {
            letter-spacing: -0.02em;
        }
        [data-testid="stSidebar"] {
            background: #11172a;
            border-right: 1px solid rgba(255,255,255,0.08);
        }
        .soft-card {
            padding: 1rem 1.1rem;
            border: 1px solid rgba(255,255,255,0.10);
            background: rgba(255,255,255,0.03);
            border-radius: 18px;
            margin-bottom: 1rem;
        }
        .muted {
            color: #a7b0c3;
            font-size: 0.92rem;
        }
        .metric {
            padding: 0.95rem 1rem;
            border-radius: 16px;
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.09);
        }
        div.stButton > button, .stDownloadButton > button {
            border-radius: 12px !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
            padding: 0.55rem 0.9rem !important;
            font-weight: 600 !important;
        }
        div[data-baseweb="select"] > div, .stTextInput input, .stTextArea textarea {
            border-radius: 12px !important;
        }
        .item-title {
            font-weight: 700;
            font-size: 1.02rem;
            margin-bottom: 0.2rem;
        }
        .pill {
            display: inline-block;
            padding: 0.18rem 0.55rem;
            border-radius: 999px;
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.08);
            margin-right: 0.4rem;
            font-size: 0.78rem;
        }
        .empty {
            padding: 2rem 1.2rem;
            border-radius: 18px;
            text-align: center;
            border: 1px dashed rgba(255,255,255,0.15);
            color: #a7b0c3;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    st.markdown(
        """
        <div class="soft-card">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;flex-wrap:wrap;">
                <div>
                    <h1 style="margin:0;">Portable Work Router</h1>
                    <div class="muted">Tarea → briefing → ejecución → captura → activo portable.</div>
                </div>
                <div class="muted">v0 local • SQLite + Markdown</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_stats() -> None:
    s = stats()
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="metric"><div class="muted">Tareas</div><div style="font-size:1.6rem;font-weight:700;">{s["tasks"]}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric"><div class="muted">Assets</div><div style="font-size:1.6rem;font-weight:700;">{s["assets"]}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric"><div class="muted">Activas</div><div style="font-size:1.6rem;font-weight:700;">{s["active"]}</div></div>', unsafe_allow_html=True)


# =========================
# Views
# =========================
def view_new_task() -> None:
    st.subheader("Nueva tarea")
    with st.form("new_task_form", clear_on_submit=False):
        col1, col2 = st.columns([2, 1])
        with col1:
            title = st.text_input("Título", placeholder="Ej.: Preparar briefing para rediseño onboarding PWR")
        with col2:
            task_type = st.selectbox("Tipo de tarea", list(TASK_TYPES.keys()), index=0)

        description = st.text_area(
            "Descripción",
            placeholder="Qué necesitas conseguir con esta tarea.",
            height=120,
        )
        context = st.text_area(
            "Contexto útil",
            placeholder="Notas, restricciones, antecedentes, ideas previas, etc.",
            height=220,
        )
        tags = st.text_input("Tags", placeholder="pwr, onboarding, ux")
        submitted = st.form_submit_button("Generar briefing y guardar")

    if submitted:
        if not title.strip() or not description.strip():
            st.error("Título y descripción son obligatorios.")
            return

        task_id = create_task(title, description, task_type, context, tags)
        st.session_state["selected_task_id"] = task_id
        st.success(f"Tarea #{task_id} creada y briefing generado.")
        st.rerun()


def view_tasks() -> None:
    st.subheader("Tareas")
    c1, c2 = st.columns([2, 1])
    search = c1.text_input("Buscar", placeholder="Título, descripción o tags")
    status_filter = c2.selectbox("Estado", ["", *STATUS_OPTIONS], index=0, format_func=lambda x: "Todos" if x == "" else x)

    rows = get_tasks(search=search, only_status=status_filter)

    if not rows:
        st.markdown('<div class="empty">No hay tareas todavía.</div>', unsafe_allow_html=True)
        return

    left, right = st.columns([1.1, 1.6], gap="large")

    with left:
        st.markdown("### Lista")
        for row in rows:
            with st.container():
                st.markdown(
                    f"""
                    <div class="soft-card">
                        <div class="item-title">{row["title"]}</div>
                        <div class="muted" style="margin-bottom:0.55rem;">{row["description"][:120]}{"..." if len(row["description"]) > 120 else ""}</div>
                        <span class="pill">{row["task_type"]}</span>
                        <span class="pill">{row["status"]}</span>
                        <span class="pill">{row["suggested_model"]}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button(f"Abrir #{row['id']}", key=f"open_task_{row['id']}", use_container_width=True):
                    st.session_state["selected_task_id"] = int(row["id"])
                    st.rerun()

    with right:
        task_id = st.session_state.get("selected_task_id")
        if not task_id:
            task_id = int(rows[0]["id"])
            st.session_state["selected_task_id"] = task_id

        row = get_task(int(task_id))
        if row is None:
            st.warning("No se pudo cargar la tarea.")
            return

        st.markdown("### Workspace")

        with st.form(f"task_edit_form_{task_id}", clear_on_submit=False):
            title = st.text_input("Título", value=row["title"])
            col1, col2 = st.columns(2)
            with col1:
                task_type = st.selectbox(
                    "Tipo de tarea",
                    list(TASK_TYPES.keys()),
                    index=list(TASK_TYPES.keys()).index(row["task_type"]) if row["task_type"] in TASK_TYPES else 0,
                )
            with col2:
                status = st.selectbox(
                    "Estado",
                    STATUS_OPTIONS,
                    index=STATUS_OPTIONS.index(row["status"]) if row["status"] in STATUS_OPTIONS else 0,
                )

            description = st.text_area("Descripción", value=row["description"], height=100)
            context = st.text_area("Contexto útil", value=row["context"], height=160)

            col3, col4 = st.columns([1, 1])
            with col3:
                suggested_model = st.text_input("Modelo sugerido", value=row["suggested_model"])
            with col4:
                tags = st.text_input("Tags", value=row["tags"])

            briefing = st.text_area("Briefing", value=row["briefing"], height=260)
            llm_output = st.text_area("Output del LLM", value=row["llm_output"], height=220)
            useful_extract = st.text_area("Extracto útil / reusable", value=row["useful_extract"], height=180)

            csave, cregen = st.columns(2)
            save_btn = csave.form_submit_button("Guardar cambios", use_container_width=True)
            regen_btn = cregen.form_submit_button("Regenerar briefing", use_container_width=True)

        if regen_btn:
            briefing = generate_briefing(title, description, task_type, context)
            suggested_model = TASK_TYPES.get(task_type, "Modelo generalista")
            update_task(
                task_id=task_id,
                title=title,
                description=description,
                task_type=task_type,
                context=context,
                suggested_model=suggested_model,
                briefing=briefing,
                llm_output=llm_output,
                useful_extract=useful_extract,
                status="brief_ready",
                tags=tags,
            )
            st.success("Briefing regenerado.")
            st.rerun()

        if save_btn:
            update_task(
                task_id=task_id,
                title=title,
                description=description,
                task_type=task_type,
                context=context,
                suggested_model=suggested_model,
                briefing=briefing,
                llm_output=llm_output,
                useful_extract=useful_extract,
                status=status,
                tags=tags,
            )
            st.success("Tarea actualizada.")
            st.rerun()

        st.markdown("### Acciones")
        a1, a2, a3 = st.columns(3)
        with a1:
            st.download_button(
                "Descargar briefing",
                data=row["briefing"],
                file_name=f"briefing-task-{row['id']}.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with a2:
            task_md = Path(row["markdown_path"]) if row["markdown_path"] else None
            if task_md and task_md.exists():
                st.download_button(
                    "Descargar tarea",
                    data=task_md.read_text(encoding="utf-8"),
                    file_name=task_md.name,
                    mime="text/markdown",
                    use_container_width=True,
                )
        with a3:
            default_asset_title = f"Asset · {row['title']}"
            if st.button("Crear asset desde extracto", use_container_width=True):
                content = row["useful_extract"].strip() or row["llm_output"].strip()
                if not content:
                    st.error("No hay extracto útil ni output para convertir en asset.")
                else:
                    asset_id = create_asset(
                        task_id=int(row["id"]),
                        title=default_asset_title,
                        summary=row["description"],
                        content=content,
                    )
                    update_task(
                        task_id=task_id,
                        title=row["title"],
                        description=row["description"],
                        task_type=row["task_type"],
                        context=row["context"],
                        suggested_model=row["suggested_model"],
                        briefing=row["briefing"],
                        llm_output=row["llm_output"],
                        useful_extract=row["useful_extract"],
                        status="executed",
                        tags=row["tags"],
                    )
                    st.success(f"Asset #{asset_id} creado.")
                    st.rerun()


def view_assets() -> None:
    st.subheader("Assets")
    rows = get_assets()

    if not rows:
        st.markdown('<div class="empty">Todavía no hay assets creados.</div>', unsafe_allow_html=True)
        return

    for row in rows:
        with st.expander(f'{row["title"]} · desde "{row["task_title"]}"', expanded=False):
            st.markdown(f"**Resumen**  \n{row['summary'] or 'Sin resumen.'}")
            st.markdown(f"**Contenido**  \n{row['content']}")
            if row["markdown_path"] and Path(row["markdown_path"]).exists():
                content = Path(row["markdown_path"]).read_text(encoding="utf-8")
                st.download_button(
                    f"Descargar asset #{row['id']}",
                    data=content,
                    file_name=Path(row["markdown_path"]).name,
                    mime="text/markdown",
                    key=f"asset_download_{row['id']}",
                )


def view_home() -> None:
    st.subheader("Resumen")
    st.markdown(
        """
        <div class="soft-card">
            <div class="item-title">Qué hace esta v0</div>
            <div class="muted">
                Crea tareas estructuradas, propone modelo, genera briefing, captura el resultado del LLM
                y lo convierte en un activo portable guardado en SQLite y Markdown.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    rows = get_tasks()
    if rows:
        latest = rows[0]
        st.markdown(
            f"""
            <div class="soft-card">
                <div class="item-title">Última tarea</div>
                <div style="margin-bottom:0.4rem;">{latest["title"]}</div>
                <div class="muted">{latest["description"]}</div>
                <div style="margin-top:0.7rem;">
                    <span class="pill">{latest["task_type"]}</span>
                    <span class="pill">{latest["status"]}</span>
                    <span class="pill">{latest["suggested_model"]}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<div class="empty">Empieza creando tu primera tarea.</div>', unsafe_allow_html=True)


# =========================
# App
# =========================
def main() -> None:
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    init_db()
    inject_css()

    with st.sidebar:
        st.markdown("## Portable Work Router")
        page = st.radio(
            "Navegación",
            ["Inicio", "Nueva tarea", "Tareas", "Assets"],
            label_visibility="collapsed",
        )
        st.caption("Local-first · portable by default")

    render_header()
    render_stats()
    st.write("")

    if page == "Inicio":
        view_home()
    elif page == "Nueva tarea":
        view_new_task()
    elif page == "Tareas":
        view_tasks()
    elif page == "Assets":
        view_assets()


if __name__ == "__main__":
    main()
