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
UPLOADS_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "pwr.db"

TIPOS_TAREA = ["Pensar", "Escribir", "Programar", "Revisar", "Decidir"]


def ensure_dirs() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    UPLOADS_DIR.mkdir(exist_ok=True)


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


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


def ensure_column(conn: sqlite3.Connection, table: str, column: str, definition_sql: str) -> None:
    cols = [row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition_sql}")


def init_db() -> None:
    ensure_dirs()
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                objective TEXT DEFAULT '',
                base_context TEXT DEFAULT '',
                base_instructions TEXT DEFAULT '',
                tags_json TEXT DEFAULT '[]',
                is_favorite INTEGER DEFAULT 0,
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
                project_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                task_type TEXT DEFAULT 'Pensar',
                context TEXT DEFAULT '',
                status TEXT DEFAULT 'borrador',
                suggested_model TEXT DEFAULT '',
                router_summary TEXT DEFAULT '',
                llm_output TEXT DEFAULT '',
                useful_extract TEXT DEFAULT '',
                uploads_json TEXT DEFAULT '[]',
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
                project_id INTEGER NOT NULL,
                task_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                summary TEXT DEFAULT '',
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id),
                FOREIGN KEY(task_id) REFERENCES tasks(id)
            )
            """
        )

        ensure_column(conn, "projects", "description", "TEXT DEFAULT ''")
        ensure_column(conn, "projects", "objective", "TEXT DEFAULT ''")
        ensure_column(conn, "projects", "base_context", "TEXT DEFAULT ''")
        ensure_column(conn, "projects", "base_instructions", "TEXT DEFAULT ''")
        ensure_column(conn, "projects", "tags_json", "TEXT DEFAULT '[]'")
        ensure_column(conn, "projects", "is_favorite", "INTEGER DEFAULT 0")
        ensure_column(conn, "projects", "created_at", "TEXT DEFAULT ''")
        ensure_column(conn, "projects", "updated_at", "TEXT DEFAULT ''")

        ensure_column(conn, "project_documents", "mime_type", "TEXT DEFAULT ''")
        ensure_column(conn, "project_documents", "size_bytes", "INTEGER DEFAULT 0")
        ensure_column(conn, "project_documents", "created_at", "TEXT DEFAULT ''")
        ensure_column(conn, "project_documents", "updated_at", "TEXT DEFAULT ''")

        ensure_column(conn, "tasks", "project_id", "INTEGER")
        ensure_column(conn, "tasks", "description", "TEXT DEFAULT ''")
        ensure_column(conn, "tasks", "task_type", "TEXT DEFAULT 'Pensar'")
        ensure_column(conn, "tasks", "context", "TEXT DEFAULT ''")
        ensure_column(conn, "tasks", "status", "TEXT DEFAULT 'borrador'")
        ensure_column(conn, "tasks", "suggested_model", "TEXT DEFAULT ''")
        ensure_column(conn, "tasks", "router_summary", "TEXT DEFAULT ''")
        ensure_column(conn, "tasks", "llm_output", "TEXT DEFAULT ''")
        ensure_column(conn, "tasks", "useful_extract", "TEXT DEFAULT ''")
        ensure_column(conn, "tasks", "uploads_json", "TEXT DEFAULT '[]'")
        ensure_column(conn, "tasks", "created_at", "TEXT DEFAULT ''")
        ensure_column(conn, "tasks", "updated_at", "TEXT DEFAULT ''")

        ensure_column(conn, "assets", "project_id", "INTEGER")
        ensure_column(conn, "assets", "summary", "TEXT DEFAULT ''")
        ensure_column(conn, "assets", "created_at", "TEXT DEFAULT ''")

        count = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        if count == 0:
            created = now_iso()
            conn.executemany(
                """
                INSERT INTO projects (
                    name, description, objective, base_context, base_instructions,
                    tags_json, is_favorite, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        "Portable Work Router",
                        "Router de trabajo con múltiples LLM.",
                        "Organizar tareas, contexto y activos portables.",
                        "Proyecto centrado en ordenar trabajo con LLMs para heavy users fuera del IDE.",
                        "Todo en castellano. Sin emojis. Estética sobria B2B.",
                        json.dumps(["pwr", "producto", "ia"], ensure_ascii=False),
                        1,
                        created,
                        created,
                    ),
                    (
                        "RosmarOps",
                        "SEO adversarial y ciberseguridad.",
                        "Explorar contenidos, herramientas y posicionamiento.",
                        "Proyecto centrado en SEO adversarial, seguridad y contenidos técnicos.",
                        "Priorizar claridad técnica y tono sobrio.",
                        json.dumps(["rosmarops", "seo", "seguridad"], ensure_ascii=False),
                        1,
                        created,
                        created,
                    ),
                ],
            )


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
        saved.append({
            "name": name,
            "path": str(target),
            "size": len(f.getbuffer()),
            "mime_type": f.type or mimetypes.guess_type(name)[0] or "application/octet-stream",
        })
    return saved


def save_task_files(project_id: int, task_id: int, files) -> List[Dict]:
    dest = project_upload_dir(project_id) / f"task_{task_id:04d}"
    dest.mkdir(parents=True, exist_ok=True)
    saved = []
    for f in files or []:
        name = Path(f.name).name
        target = dest / name
        target.write_bytes(f.getbuffer())
        saved.append({
            "name": name,
            "path": str(target),
            "size": len(f.getbuffer()),
            "mime_type": f.type or mimetypes.guess_type(name)[0] or "application/octet-stream",
        })
    return saved


def get_projects() -> List[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT p.*,
                   (SELECT COUNT(*) FROM tasks t WHERE t.project_id = p.id) AS task_count,
                   (SELECT COUNT(*) FROM assets a WHERE a.project_id = p.id) AS asset_count
            FROM projects p
            ORDER BY p.is_favorite DESC, p.updated_at DESC, p.id DESC
            """
        ).fetchall()


def get_project(project_id: int) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()


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
                name.strip(),
                description.strip(),
                objective.strip(),
                base_context.strip(),
                base_instructions.strip(),
                json.dumps([t.strip() for t in tags.split(",") if t.strip()], ensure_ascii=False),
                now_iso(),
                project_id,
            ),
        )


def set_favorite(project_id: int, is_favorite: bool) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE projects SET is_favorite = ?, updated_at = ? WHERE id = ?",
            (1 if is_favorite else 0, now_iso(), project_id),
        )


def create_project(name: str, description: str, objective: str, base_context: str, base_instructions: str, tags: str, uploaded_files) -> int:
    created = now_iso()
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO projects (
                name, description, objective, base_context, base_instructions,
                tags_json, is_favorite, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)
            """,
            (
                name.strip(),
                description.strip(),
                objective.strip(),
                base_context.strip(),
                base_instructions.strip(),
                json.dumps([t.strip() for t in tags.split(",") if t.strip()], ensure_ascii=False),
                created,
                created,
            ),
        )
        pid = int(cur.lastrowid)
        saved = save_project_files(pid, uploaded_files)
        for item in saved:
            conn.execute(
                """
                INSERT INTO project_documents (
                    project_id, title, file_name, file_path, mime_type, size_bytes, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pid, item["name"], item["name"], item["path"], item["mime_type"],
                    item["size"], created, created,
                ),
            )
        return pid


def get_project_documents(project_id: int) -> List[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM project_documents WHERE project_id = ? ORDER BY updated_at DESC, id DESC",
            (project_id,),
        ).fetchall()


def score_model(task_type: str, text: str, inherited_context: str, project_docs: List[sqlite3.Row], task_files: List[Dict]) -> Dict:
    combined = f"{text} {inherited_context}".lower()
    scores = {"Claude Sonnet": 0, "ChatGPT": 0, "Codex": 0, "Gemini": 0}
    reasons = []

    def add(model: str, points: int, reason: str):
        scores[model] += points
        reasons.append((model, points, reason))

    if task_type == "Programar" or any(k in combined for k in ["python", "api", "bug", "sql", "código", "deploy"]):
        add("Codex", 6, "La tarea tiene señales técnicas o de programación.")
    if task_type == "Escribir" or any(k in combined for k in ["mensaje", "narrativa", "contenido", "estrategia", "editorial"]):
        add("Claude Sonnet", 5, "La tarea pide redacción estructurada o criterio editorial.")
    if task_type == "Pensar" or any(k in combined for k in ["ideas", "opciones", "brainstorm", "hipótesis", "explorar"]):
        add("ChatGPT", 4, "La tarea parece de exploración o generación de opciones.")
        add("Claude Sonnet", 2, "También puede ayudar a ordenar mejor la reflexión.")
    if task_type == "Decidir":
        add("ChatGPT", 4, "La tarea parece orientada a comparar y decidir rápido.")
        add("Claude Sonnet", 2, "Puede ayudar a estructurar trade-offs.")
    if task_type == "Revisar":
        add("Claude Sonnet", 4, "La tarea parece de revisión o lectura crítica.")
    if len(inherited_context.strip()) > 300:
        add("Claude Sonnet", 2, "Hay bastante contexto heredado y conviene profundidad.")
    if project_docs:
        add("Claude Sonnet", 2, "El proyecto ya tiene documentación de referencia asociada.")
    if task_files:
        add("Claude Sonnet", 2, "La tarea incluye adjuntos y conviene una lectura estructurada.")
        add("Gemini", 1, "Puede servir como lectura alternativa o contraste.")

    ranking = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    recommended = ranking[0][0]
    top_reasons = [r for m, _, r in reasons if m == recommended][:3]
    fit = "alto" if ranking[0][1] - ranking[1][1] >= 3 else "medio"

    return {
        "recommended_model": recommended,
        "fit": fit,
        "scores": scores,
        "reasons": top_reasons,
    }


def create_task(project_id: int, title: str, description: str, task_type: str, context: str, uploaded_files) -> int:
    created = now_iso()
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO tasks (
                project_id, title, description, task_type, context, status,
                suggested_model, router_summary, llm_output, useful_extract, uploads_json, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, 'router_listo', '', '', '', '', '[]', ?, ?)
            """,
            (project_id, title.strip(), description.strip(), task_type, context.strip(), created, created),
        )
        tid = int(cur.lastrowid)

        project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        docs = conn.execute("SELECT * FROM project_documents WHERE project_id = ?", (project_id,)).fetchall()
        task_files = save_task_files(project_id, tid, uploaded_files)
        router = score_model(task_type, f"{title} {description} {context}", project["base_context"], docs, task_files)

        summary = "Modelo recomendado: {}\nNivel de ajuste: {}\n\nMotivos:\n{}".format(
            router["recommended_model"],
            router["fit"],
            "\n".join([f"- {r}" for r in router["reasons"]]) if router["reasons"] else "- Sin motivos destacados",
        )

        conn.execute(
            """
            UPDATE tasks
            SET suggested_model = ?, router_summary = ?, uploads_json = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                router["recommended_model"],
                summary,
                json.dumps(task_files, ensure_ascii=False),
                now_iso(),
                tid,
            ),
        )
        return tid


def get_project_tasks(project_id: int, search: str = "") -> List[sqlite3.Row]:
    with get_conn() as conn:
        if search.strip():
            pattern = f"%{search.strip()}%"
            return conn.execute(
                """
                SELECT * FROM tasks
                WHERE project_id = ? AND (title LIKE ? OR description LIKE ? OR context LIKE ?)
                ORDER BY updated_at DESC, id DESC
                """,
                (project_id, pattern, pattern, pattern),
            ).fetchall()
        return conn.execute(
            "SELECT * FROM tasks WHERE project_id = ? ORDER BY updated_at DESC, id DESC",
            (project_id,),
        ).fetchall()


def get_task(task_id: int) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()


def update_task_result(task_id: int, llm_output: str, useful_extract: str) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE tasks
            SET llm_output = ?, useful_extract = ?, status = 'ejecutado', updated_at = ?
            WHERE id = ?
            """,
            (llm_output, useful_extract, now_iso(), task_id),
        )


def create_asset(project_id: int, task_id: int, title: str, summary: str, content: str) -> int:
    created = now_iso()
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO assets (project_id, task_id, title, summary, content, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (project_id, task_id, title.strip(), summary.strip(), content.strip(), created),
        )
        return int(cur.lastrowid)


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


def inject_css():
    st.markdown(
        """
        <style>
        .stApp { background: #F7F9FC; color: #0F172A; }
        .block-container { max-width: 1480px; padding-top: 1rem; padding-bottom: 1.4rem; padding-left: 1.2rem; padding-right: 1.2rem; }
        [data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid #E2E8F0; }
        [data-testid="stSidebar"] * { color: #0F172A !important; }
        .card, .panel { background:#FFFFFF; border:1px solid #E2E8F0; border-radius:18px; padding:1rem 1.1rem; box-shadow:0 1px 2px rgba(15,23,42,0.04); }
        .card { margin-bottom: 0.85rem; }
        .muted { color:#475569; font-size:0.92rem; }
        .meta { color:#94A3B8; font-size:0.82rem; }
        .pill { display:inline-block; padding:0.15rem 0.5rem; border-radius:999px; border:1px solid #E2E8F0; background:#FFF; color:#475569; font-size:0.76rem; margin-right:0.35rem; }
        .metric { background:#FFF; border:1px solid #E2E8F0; border-radius:16px; padding:0.85rem 0.95rem; }
        .task-row, .project-row { background:#FFF; border:1px solid #E2E8F0; border-radius:14px; padding:0.8rem 0.9rem; margin-bottom:0.65rem; }
        .task-row.selected { border:2px solid #1E293B; }
        div[data-baseweb="select"] > div, .stTextInput input, .stTextArea textarea { border-radius:12px !important; border:1px solid #E2E8F0 !important; background:#FFF !important; color:#0F172A !important; }
        div.stButton > button, .stDownloadButton > button { border-radius:12px !important; border:1px solid #CBD5E1 !important; background:#FFF !important; color:#0F172A !important; padding:0.55rem 0.9rem !important; font-weight:600 !important; }
        div.stButton > button:hover, .stDownloadButton > button:hover { border-color:#94A3B8 !important; background:#F8FAFC !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def project_selector():
    projects = get_projects()
    names = [p["name"] for p in projects]
    selected_project_id = st.session_state.get("active_project_id")
    default_index = 0
    options = ["Seleccionar proyecto"] + names
    if selected_project_id:
        current = get_project(selected_project_id)
        if current and current["name"] in names:
            default_index = names.index(current["name"]) + 1

    selected_name = st.selectbox("Proyecto activo", options, index=default_index)
    if selected_name != "Seleccionar proyecto":
        for p in projects:
            if p["name"] == selected_name:
                st.session_state["active_project_id"] = p["id"]
                break


def render_header():
    projects = get_projects()
    total_tasks = sum([p["task_count"] for p in projects])
    total_assets = sum([p["asset_count"] for p in projects])

    c1, c2 = st.columns([2.2, 1.4])
    with c1:
        st.markdown(
            """
            <div class="card">
                <h1 style="margin:0;">Portable Work Router</h1>
                <div class="muted">Selecciona un proyecto, captura una tarea y conviértela en trabajo reusable.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        m1, m2, m3 = st.columns(3)
        m1.markdown(f'<div class="metric"><div class="meta">Proyectos</div><div style="font-size:1.35rem;font-weight:700;">{len(projects)}</div></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="metric"><div class="meta">Tareas</div><div style="font-size:1.35rem;font-weight:700;">{total_tasks}</div></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="metric"><div class="meta">Activos</div><div style="font-size:1.35rem;font-weight:700;">{total_assets}</div></div>', unsafe_allow_html=True)


def home_view():
    st.subheader("Acceso rápido")
    projects = get_projects()
    favorites = [p for p in projects if p["is_favorite"] == 1]

    c1, c2 = st.columns([1.1, 1], gap="large")
    with c1:
        st.markdown("### Favoritos")
        if not favorites:
            st.write("Todavía no hay favoritos.")
        for p in favorites:
            r1, r2 = st.columns([5, 1])
            with r1:
                st.markdown(f"**{p['name']}**")
                st.caption(p["description"] or "Sin descripción.")
            with r2:
                if st.button("Abrir", key=f"fav_open_{p['id']}", use_container_width=True):
                    st.session_state["active_project_id"] = p["id"]
                    st.rerun()

        st.markdown("---")
        st.markdown("### Buscar proyecto")
        search = st.text_input("Buscar", placeholder="Nombre del proyecto")
        results = [p for p in projects if search.lower() in p["name"].lower()] if search else projects[:8]
        for p in results:
            r1, r2, r3 = st.columns([4.5, 1, 1])
            with r1:
                st.write(p["name"])
            with r2:
                if st.button("Abrir", key=f"search_open_{p['id']}", use_container_width=True):
                    st.session_state["active_project_id"] = p["id"]
                    st.rerun()
            with r3:
                label = "Quitar" if p["is_favorite"] == 1 else "Fijar"
                if st.button(label, key=f"fav_toggle_{p['id']}", use_container_width=True):
                    set_favorite(p["id"], p["is_favorite"] == 0)
                    st.rerun()

    with c2:
        with st.expander("Crear proyecto nuevo"):
            name = st.text_input("Nombre del proyecto", placeholder="Ej.: Cognitive OS")
            description = st.text_area("Descripción breve", height=80)
            objective = st.text_area("Objetivo del proyecto", height=80)
            base_context = st.text_area("Contexto de referencia del proyecto", height=120)
            base_instructions = st.text_area("Reglas estables del proyecto", height=110)
            tags = st.text_input("Etiquetas", placeholder="producto, ia, trabajo")
            files = st.file_uploader("Documentos de referencia del proyecto", accept_multiple_files=True)
            if st.button("Dar de alta el proyecto", use_container_width=True):
                if not name.strip():
                    st.error("El nombre del proyecto es obligatorio.")
                else:
                    pid = create_project(name, description, objective, base_context, base_instructions, tags, files)
                    st.session_state["active_project_id"] = pid
                    st.rerun()


def project_view():
    pid = st.session_state.get("active_project_id")
    if not pid:
        st.info("Selecciona un proyecto.")
        return

    project = get_project(pid)
    if not project:
        st.warning("No se pudo cargar el proyecto.")
        return

    tags = ", ".join(safe_json_loads(project["tags_json"], []))
    docs = get_project_documents(pid)
    tasks = get_project_tasks(pid)
    assets = get_project_assets(pid)

    h1, h2 = st.columns([5.5, 1])
    with h1:
        st.markdown(f"## {project['name']}")
        st.caption(project["description"] or "Sin descripción.")
    with h2:
        if st.button("Salir", use_container_width=True):
            st.session_state["active_project_id"] = None
            st.rerun()

    st.markdown(
        f"""
        <div class="card">
            <span class="pill">{len(tasks)} tareas</span>
            <span class="pill">{len(assets)} activos</span>
            <span class="pill">{len(docs)} documentos</span>
            {f'<span class="pill">{tags}</span>' if tags else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )

    exp_key = f"show_project_info_{pid}"
    edit_key = f"edit_project_info_{pid}"
    if exp_key not in st.session_state:
        st.session_state[exp_key] = False
    if edit_key not in st.session_state:
        st.session_state[edit_key] = False

    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("Ocultar ficha del proyecto" if st.session_state[exp_key] else "Mostrar ficha del proyecto", use_container_width=True):
            st.session_state[exp_key] = not st.session_state[exp_key]
            if not st.session_state[exp_key]:
                st.session_state[edit_key] = False
            st.rerun()
    with c2:
        if st.session_state[exp_key]:
            st.session_state[edit_key] = st.toggle("Editar ficha del proyecto", value=st.session_state[edit_key], key=f"edit_toggle_{pid}")

    if st.session_state[exp_key]:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        if not st.session_state[edit_key]:
            st.markdown("### Ficha del proyecto")
            st.markdown("**Objetivo del proyecto**")
            st.write(project["objective"] or "Sin objetivo definido.")
            st.markdown("**Contexto de referencia del proyecto**")
            st.write(project["base_context"] or "Sin contexto base definido.")
            st.markdown("**Reglas estables del proyecto**")
            st.write(project["base_instructions"] or "Sin reglas estables definidas.")
        else:
            name = st.text_input("Nombre del proyecto", value=project["name"])
            description = st.text_area("Descripción breve", value=project["description"], height=80)
            objective = st.text_area("Objetivo del proyecto", value=project["objective"], height=80)
            base_context = st.text_area("Contexto de referencia del proyecto", value=project["base_context"], height=140)
            base_instructions = st.text_area("Reglas estables del proyecto", value=project["base_instructions"], height=120)
            tags_value = ", ".join(safe_json_loads(project["tags_json"], []))
            tags = st.text_input("Etiquetas", value=tags_value)
            b1, b2 = st.columns(2)
            with b1:
                if st.button("Guardar cambios del proyecto", use_container_width=True):
                    update_project(pid, name, description, objective, base_context, base_instructions, tags)
                    st.session_state[edit_key] = False
                    st.rerun()
            with b2:
                if st.button("Cancelar edición", use_container_width=True):
                    st.session_state[edit_key] = False
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    left, right = st.columns([1.1, 1.9], gap="large")

    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("### Captura rápida")
        title = st.text_input("Título de la tarea", placeholder="Ej.: Revisar flujo de captura")
        task_type = st.selectbox("Tipo de trabajo", TIPOS_TAREA)
        description = st.text_area("¿Qué necesitas hacer?", height=120, placeholder="Describe brevemente la tarea.")
        context = st.text_area("Contexto específico", height=120, placeholder="Notas, restricciones o antecedentes puntuales.")
        files = st.file_uploader("Adjuntar documentos de tarea", accept_multiple_files=True, key=f"task_files_{pid}")
        if files:
            for f in files:
                st.markdown(f"- {f.name} ({human_size(f.size)})")
        if st.button("Crear tarea", use_container_width=True):
            if not title.strip() and description.strip():
                title = description.strip()[:80]
            if not (title.strip() and description.strip()):
                st.error("Título y descripción son obligatorios.")
            else:
                tid = create_task(pid, title, description, task_type, context, files)
                st.session_state["selected_task_id"] = tid
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.write("")
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("### Tareas")
        search = st.text_input("Buscar en tus tareas", placeholder="Título o contenido", key=f"search_tasks_{pid}")
        filtered = get_project_tasks(pid, search=search)
        selected_tid = st.session_state.get("selected_task_id")
        if not filtered:
            st.write("Todavía no hay tareas.")
        for t in filtered:
            selected_class = " selected" if t["id"] == selected_tid else ""
            st.markdown(
                f"""
                <div class="task-row{selected_class}">
                    <div style="font-weight:700;">{t["title"]}</div>
                    <div class="muted" style="margin-top:0.2rem;">{t["description"][:88]}{"..." if len(t["description"]) > 88 else ""}</div>
                    <div style="margin-top:0.45rem;">
                        <span class="pill">{t["task_type"]}</span>
                        <span class="pill">{t["suggested_model"] or "Sin router"}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Abrir", key=f"open_task_{t['id']}", use_container_width=True):
                st.session_state["selected_task_id"] = t["id"]
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        tid = st.session_state.get("selected_task_id")
        if not tid:
            st.info("Selecciona o crea una tarea para trabajar.")
            return

        task = get_task(tid)
        if not task or task["project_id"] != pid:
            st.info("Selecciona una tarea válida del proyecto.")
            return

        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("### Tarea")
        st.markdown(f"**{task['title']}**")
        st.caption(task["description"])

        st.markdown("### Decisión de modelo")
        st.markdown(f"**{task['suggested_model'] or 'Sin recomendación'}**")
        st.text(task["router_summary"] or "Sin resumen del router.")

        st.markdown("### Prompt sugerido")
        prompt = f"""PROYECTO
{project['name']}

TAREA
{task['title']}

OBJETIVO
{task['description']}

CONTEXTO HEREDADO
{project['base_context'] or 'Sin contexto base.'}

CONTEXTO DE TAREA
{task['context'] or 'Sin contexto específico.'}

INSTRUCCIÓN
Ayúdame a resolver esta tarea de forma clara, estructurada y accionable.
"""
        st.code(prompt)

        st.markdown("### Resultado")
        output = st.text_area("Pega aquí el resultado del modelo", value=task["llm_output"], height=200)
        extract = st.text_area("Extracto reusable", value=task["useful_extract"], height=140)

        b1, b2 = st.columns(2)
        with b1:
            if st.button("Guardar resultado", use_container_width=True):
                update_task_result(tid, output, extract)
                st.rerun()
        with b2:
            if st.button("Crear activo", use_container_width=True):
                final_content = extract.strip() or output.strip()
                if not final_content:
                    st.error("No hay contenido para convertir en activo.")
                else:
                    create_asset(pid, tid, f"Activo · {task['title']}", task["description"], final_content)
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

        st.write("")
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("### Activos recientes del proyecto")
        if not assets:
            st.write("Todavía no hay activos.")
        for a in assets[:5]:
            st.markdown(f"**{a['title']}**")
            st.caption(a["summary"] or "Sin resumen.")
        st.markdown('</div>', unsafe_allow_html=True)


def main():
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    init_db()
    inject_css()

    with st.sidebar:
        st.markdown("## Portable Work Router")
        project_selector()
        st.caption("Diseño sobrio · proyectos persistentes · flujo de trabajo real")

    render_header()
    st.write("")

    if st.session_state.get("active_project_id"):
        project_view()
    else:
        home_view()


if __name__ == "__main__":
    main()
