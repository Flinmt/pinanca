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

    for key, default in (
        ("cpf_input", ""),
        ("cpf_digits", ""),
        ("cpf_input_widget", ""),
    ):
        st.session_state.setdefault(key, default)

    def _format_cpf_mask(d: str) -> str:
        if len(d) <= 3:
            return d
        if len(d) <= 6:
            return f"{d[:3]}.{d[3:]}"
        if len(d) <= 9:
            return f"{d[:3]}.{d[3:6]}.{d[6:]}"
        return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:11]}"

    password_value = ""

    left, center, right = st.columns([1, 2, 1])
    with center:
        form = st.form("login_form", clear_on_submit=False, border=True)
        with form:
            raw_cpf = st.text_input(
                "CPF",
                key="cpf_input_widget",
                help="Apenas dígitos (máx. 11)",
            )
            digits = "".join(ch for ch in raw_cpf if ch.isdigit())[:11]
            st.session_state["cpf_digits"] = digits
            masked = _format_cpf_mask(digits)
            st.session_state["cpf_input"] = masked
            st.session_state["cpf_input_widget"] = masked

            password_value = st.text_input("Senha", type="password", key="login_password")

    with center:
        submitted = form.form_submit_button(
            "Entrar", type="primary", use_container_width=True
        )

    if submitted:
        try:
            cpf_value = st.session_state.get("cpf_digits", "")
            password = st.session_state.get("login_password", password_value)
            login_and_persist(cpf_value, password)
            st.success("Login realizado com sucesso!")
            if hasattr(st, "switch_page"):
                st.switch_page("pages/dashboard.py")
            else:
                _do_rerun()
        except Exception as e:
            st.error(str(e))

render()
