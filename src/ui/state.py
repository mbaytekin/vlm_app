import streamlit as st

def init_state():
    st.session_state.setdefault("selected_model_key", None)
    st.session_state.setdefault("served_name", None)
    st.session_state.setdefault("alive", False)
