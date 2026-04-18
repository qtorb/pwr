
# v6.7 – UX limpia + flujo real + jerarquía visible

import streamlit as st
from datetime import datetime

st.set_page_config(layout="wide")

# ---------- STATE ----------
if "projects" not in st.session_state:
    st.session_state.projects = [
        {"id":1,"name":"Portable Work Router","desc":"Router LLMs"},
        {"id":2,"name":"RosmarOps","desc":"SEO adversarial"},
    ]

if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "active_project_id" not in st.session_state:
    st.session_state.active_project_id = None

if "selected_task_id" not in st.session_state:
    st.session_state.selected_task_id = None


# ---------- ROUTER ----------
def simple_router(text):
    text = text.lower()
    if any(k in text for k in ["python","api","bug","código"]):
        return "Codex"
    if any(k in text for k in ["estrategia","mensaje","narrativa"]):
        return "Claude"
    if any(k in text for k in ["ideas","opciones","brainstorm"]):
        return "ChatGPT"
    return "ChatGPT"


# ---------- HELPERS ----------
def get_project(pid):
    return next((p for p in st.session_state.projects if p["id"] == pid), None)


def get_tasks(pid):
    return [t for t in st.session_state.tasks if t["project_id"] == pid]


# ---------- HOME ----------
st.title("Portable Work Router")

if st.session_state.active_project_id is None:

    st.subheader("¿En qué proyecto quieres trabajar?")

    for p in st.session_state.projects:
        c1, c2 = st.columns([6,1])
        with c1:
            st.markdown(f"### {p['name']}")
            st.caption(p["desc"])
        with c2:
            if st.button("Abrir", key=f"open_{p['id']}"):
                st.session_state.active_project_id = p["id"]
                st.rerun()

    st.markdown("---")

    with st.expander("Crear proyecto nuevo"):
        name = st.text_input("Nombre")
        desc = st.text_input("Descripción")
        if st.button("Crear proyecto"):
            st.session_state.projects.append(
                {"id":len(st.session_state.projects)+1,"name":name,"desc":desc}
            )
            st.rerun()


# ---------- WORKSPACE ----------
else:

    project = get_project(st.session_state.active_project_id)

    # HEADER
    col1, col2 = st.columns([6,1])
    with col1:
        st.markdown(f"## {project['name']}")
        st.caption(project["desc"])
    with col2:
        if st.button("Cambiar"):
            st.session_state.active_project_id = None
            st.rerun()

    st.markdown("---")

    # LAYOUT
    left, right = st.columns([1.2, 2])

    # ---------- LEFT: CAPTURE ----------
    with left:
        st.markdown("### Captura rápida")

        text = st.text_area(
            "¿Qué necesitas hacer?",
            placeholder="Escribe una tarea, idea o instrucción..."
        )

        if st.button("Crear tarea", use_container_width=True):
            if text.strip():
                model = simple_router(text)

                task = {
                    "id": len(st.session_state.tasks)+1,
                    "project_id": project["id"],
                    "text": text,
                    "model": model,
                    "created": datetime.now().strftime("%H:%M"),
                }

                st.session_state.tasks.append(task)
                st.session_state.selected_task_id = task["id"]
                st.rerun()

        st.markdown("---")

        st.markdown("### Tareas")

        tasks = get_tasks(project["id"])

        for t in reversed(tasks):
            if st.button(
                f"{t['text'][:40]}... ({t['model']})",
                key=f"task_{t['id']}",
                use_container_width=True
            ):
                st.session_state.selected_task_id = t["id"]
                st.rerun()

    # ---------- RIGHT: WORK ----------
    with right:

        if st.session_state.selected_task_id is None:
            st.info("Selecciona o crea una tarea")
        else:
            task = next(t for t in st.session_state.tasks if t["id"] == st.session_state.selected_task_id)

            st.markdown("### Tarea")

            st.markdown(f"**{task['text']}**")
            st.caption(f"Modelo recomendado: {task['model']}")

            st.markdown("---")

            st.markdown("### Prompt sugerido")

            prompt = f"""TAREA:
{task['text']}

INSTRUCCIÓN:
Ayúdame a resolver esto de forma clara y estructurada.
"""
            st.code(prompt)

            st.markdown("---")

            st.markdown("### Resultado")

            st.text_area("Pega aquí el resultado del modelo", height=200)
