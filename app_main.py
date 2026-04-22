import streamlit as st
import os

st.set_page_config(page_title="PWR Test", layout="wide")

if os.environ.get("PORT"):
    st.warning("🔧 Running on Railway (ephemeral storage)")

st.title("✅ Streamlit OK")
st.write(f"Port: {os.environ.get('PORT', 'local')}")
st.write("Backend is responding correctly.")
