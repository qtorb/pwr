import streamlit as st

st.set_page_config(page_title="PWR Minimal Test", layout="wide")

st.title("✅ PWR Minimal Test")
st.write("App loaded successfully - no imports, no DB, no router.")

if st.button("Test Button"):
    st.success("Button works - websocket connected!")

st.info(f"Streamlit version: {st.__version__}")
