
# v6.6 – captura rápida conectada a tareas + router (simplificado pero funcional)

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

if "active_project" not in st.session_state:
    st.session_state.active_project = None


# ---------- SIMPLE ROUTER ----------
def simple_router(text):
    text = text.lower()
    if any(k in text for k in ["código","python","api","bug"]):
        return "Codex"
    if any(k in text for k in ["estrategia","mensaje","narrativa"]):
        return "Claude"
    if any(k in text for k in ["ideas","opciones","brainstorm"]):
        return "ChatGPT"
    return "ChatGPT"


# ---------- HOME ----------
st.title("Portable Work Router")

if st.session_state.active_project is None:

    st.subheader("Seleccionar proyecto")

    for p in st.session_state.projects:
        col1, col2 = st.columns([4,1])
        with col1:
            st.markdown(f"**{p['name']}**  \n{p['desc']}")
        with col2:
            if st.button("Abrir", key=f"open_{p['id']}"):
                st.session_state.active_project = p
                st.rerun()

    st.markdown("---")

    with st.expander("Crear nuevo proyecto"):
        name = st.text_input("Nombre")
        desc = st.text_input("Descripción")
        if st.button("Crear"):
            st.session_state.projects.append(
                {"id":len(st.session_state.projects)+1,"name":name,"desc":desc}
            )
            st.rerun()


# ---------- WORKSPACE ----------
else:
    p = st.session_state.active_project

    col1, col2 = st.columns([5,1])
    with col1:
        st.subheader(p["name"])
        st.caption(p["desc"])
    with col2:
        if st.button("Cambiar proyecto"):
            st.session_state.active_project = None
            st.rerun()

    # ---------- CAPTURA RÁPIDA ----------
    st.markdown("## Captura rápida")

    text = st.text_area("¿Qué necesitas hacer?")

    if st.button("Crear tarea"):
        if text.strip() == "":
            st.warning("Escribe algo")
        else:
            model = simple_router(text)

            task = {
                "id": len(st.session_state.tasks)+1,
                "project": p["name"],
                "text": text,
                "model": model,
                "created": datetime.now().strftime("%H:%M:%S")
            }

            st.session_state.tasks.append(task)
            st.success(f"Tarea creada → modelo recomendado: {model}")
            st.rerun()

    st.markdown("---")

    # ---------- LISTA DE TRABAJO ----------
    st.subheader("Trabajo reciente")

    project_tasks = [t for t in st.session_state.tasks if t["project"] == p["name"]]

    if not project_tasks:
        st.write("Sin tareas todavía")
    else:
        for t in reversed(project_tasks):

            with st.container():
                col1, col2 = st.columns([5,1])

                with col1:
                    st.markdown(f"**{t['text']}**")
                    st.caption(f"{t['created']} · {t['model']}")

                with col2:
                    if st.button("Abrir", key=f"task_{t['id']}"):
                        st.session_state["selected_task"] = t

    # ---------- DETALLE ----------
    if "selected_task" in st.session_state:

        st.markdown("---")
        st.subheader("Detalle de tarea")

        t = st.session_state["selected_task"]

        st.markdown(f"### {t['text']}")
        st.write(f"Modelo recomendado: **{t['model']}**")

        st.text_area("Resultado (simulado)")

