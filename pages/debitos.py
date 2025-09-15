from __future__ import annotations
import streamlit as st
from core.session import current_user
from ui.nav import render_sidebar


def render(user=None):
    user = user or current_user()
    if not user:
        if hasattr(st, "switch_page"):
            st.switch_page("pages/login.py")
        else:
            st.stop()
    render_sidebar(user)
    st.title("Débitos")
    st.write("Tela de Débitos (em desenvolvimento).")

render()
