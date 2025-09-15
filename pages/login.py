from __future__ import annotations
import streamlit as st
from core.session import login_and_persist


def _do_rerun():
    fn = getattr(st, "rerun", None) or getattr(st, "experimental_rerun", None)
    if fn:
        fn()


def render():
    st.title("Entrar")
    st.write("Informe suas credenciais para acessar.")

    if "cpf_input" not in st.session_state:
        st.session_state["cpf_input"] = ""
    if "cpf_digits" not in st.session_state:
        st.session_state["cpf_digits"] = ""

    def _format_cpf_mask(d: str) -> str:
        if len(d) <= 3:
            return d
        if len(d) <= 6:
            return f"{d[:3]}.{d[3:]}"
        if len(d) <= 9:
            return f"{d[:3]}.{d[3:6]}.{d[6:]}"
        return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:11]}"

    def _handle_cpf_change():
        raw = st.session_state.get("cpf_input", "")
        digits = "".join(ch for ch in raw if ch.isdigit())[:11]
        st.session_state["cpf_digits"] = digits
        masked = _format_cpf_mask(digits)
        if raw != masked:
            st.session_state["cpf_input"] = masked

    st.text_input(
        "CPF",
        key="cpf_input",
        help="Apenas dígitos (máx. 11)",
        on_change=_handle_cpf_change,
    )

    password = st.text_input("Senha", type="password")
    st.markdown("<div style='height: 45px;'></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        submitted = st.button("Entrar", use_container_width=True)

    if submitted:
        try:
            cpf_value = st.session_state.get("cpf_digits", "")
            login_and_persist(cpf_value, password)
            st.success("Login realizado com sucesso!")
            if hasattr(st, "switch_page"):
                st.switch_page("pages/dashboard.py")
            else:
                _do_rerun()
        except Exception as e:
            st.error(str(e))

# Auto-render when executed as a Streamlit page
render()
