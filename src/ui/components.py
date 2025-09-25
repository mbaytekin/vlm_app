import streamlit as st

def sidebar_header(title:str):
    st.sidebar.markdown(f"### {title}")

def kv(label, value):
    st.sidebar.markdown(f"**{label}:** {value}")
