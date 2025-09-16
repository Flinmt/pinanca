from __future__ import annotations
import streamlit as st
from core.session import login_and_persist


def _do_rerun():
    fn = getattr(st, "rerun", None) or getattr(st, "experimental_rerun", None)
    if fn:
        fn()


def render():
    st.set_page_config(page_title="Entrar", layout="centered")

    st.markdown(
        """
        <div style="display:flex;flex-direction:column;align-items:center;">
          <h1>Entrar</h1>
          <p>Informe suas credenciais para acessar.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.session_state.setdefault("cpf_digits", "")
    st.session_state.setdefault("login_password", "")

    left, center, right = st.columns([1, 2, 1])
    with center:
        form = st.form("login_form", clear_on_submit=False, border=True)
        with form:
            raw_cpf = st.text_input(
                "CPF",
                help="Informe até 11 dígitos",
                key="login_cpf",
            )
            digits = "".join(ch for ch in raw_cpf if ch.isdigit())[:11]
            st.session_state["cpf_digits"] = digits

            st.text_input("Senha", type="password", key="login_password")

    with center:
        submitted = form.form_submit_button(
            "Entrar", type="primary", use_container_width=True
        )

    if submitted:
        try:
            cpf_value = st.session_state.get("cpf_digits", "")
            password = st.session_state.get("login_password", "")
            login_and_persist(cpf_value, password)
            st.success("Login realizado com sucesso!")
            if hasattr(st, "switch_page"):
                st.switch_page("pages/dashboard.py")
            else:
                _do_rerun()
        except Exception as e:
            st.error(str(e))

render()
