
# v6.5 – foco en selección de proyecto + captura rápida

import streamlit as st

st.set_page_config(layout="wide")

# fake state
if "projects" not in st.session_state:
    st.session_state.projects = [
        {"id":1,"name":"Portable Work Router","desc":"Router LLMs"},
        {"id":2,"name":"RosmarOps","desc":"SEO adversarial"},
        {"id":3,"name":"Cognitive OS","desc":"Second brain"}
    ]

if "active_project" not in st.session_state:
    st.session_state.active_project = None

st.title("Portable Work Router")

# HOME
if st.session_state.active_project is None:

    st.subheader("Seleccionar proyecto")

    for p in st.session_state.projects:
        col1, col2 = st.columns([4,1])
        with col1:
            st.markdown(f"**{p['name']}**  
{p['desc']}")
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

# WORKSPACE
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

    st.markdown("## Captura rápida")

    mode = st.radio(
        "Tipo de entrada",
        ["Texto","Documento","Imagen","Voz"],
        horizontal=True
    )

    if mode == "Texto":
        text = st.text_area("¿Qué necesitas hacer?")
        if st.button("Crear tarea"):
            st.success("Tarea creada (simulado)")

    elif mode == "Documento":
        file = st.file_uploader("Subir documento")
        if file:
            st.success("Documento cargado (simulado)")

    elif mode == "Imagen":
        img = st.file_uploader("Subir imagen")
        if img:
            st.success("Imagen cargada (simulado)")

    elif mode == "Voz":
        st.info("Entrada por voz (pendiente integración)")

    st.markdown("---")
    st.subheader("Trabajo reciente")
    st.write("Aquí aparecerán tareas/subproyectos (siguiente iteración)")
