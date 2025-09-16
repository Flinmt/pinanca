from __future__ import annotations
import base64
import mimetypes
import streamlit as st
import os
from core.session import logout


def _img_data_uri(path: str) -> str:
    try:
        mime, _ = mimetypes.guess_type(path)
        mime = mime or "image/png"
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        return f"data:{mime};base64,{b64}"
    except Exception:
        return ""


def _do_rerun():
    fn = getattr(st, "rerun", None) or getattr(st, "experimental_rerun", None)
    if fn:
        fn()


def render_sidebar(user) -> None:
    """Renders left navigation with default avatar and buttons.
    Expects to run only on authenticated pages.
    """
    default_src = _img_data_uri("utils/assets/imgs/profile.png")
    user_img_path = None
    try:
        user_img_path = getattr(user, "get_profile_image", lambda: None)()  # type: ignore[attr-defined]
    except Exception:
        user_img_path = None
    avatar_src = (
        _img_data_uri(user_img_path) if user_img_path and os.path.exists(str(user_img_path)) else default_src
    )
    st.sidebar.markdown(
        f"""
        <div style="display:flex;justify-content:center;margin-bottom:70px;margin-top:30px;">
          <div style="width:160px;height:160px;border-radius:50%;
                      box-shadow: 0 20px 30px rgba(0,0,0,0.08);
                      overflow:hidden; display:flex; align-items:center; justify-content:center;">
            <img src="{avatar_src}" alt="avatar" style="width:100%;height:100%;object-fit:cover;" />
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Buttons for each page
    if st.sidebar.button("Dashboard", width='stretch'):
        if hasattr(st, "switch_page"):
            st.switch_page("pages/dashboard.py")
        else:
            st.session_state["menu"] = "Dashboard"; _do_rerun(); return
    if st.sidebar.button("Transações", width='stretch'):
        if hasattr(st, "switch_page"):
            st.switch_page("pages/transacoes.py")
        else:
            st.session_state["menu"] = "Transações"; _do_rerun(); return
    if st.sidebar.button("Débitos", width='stretch'):
        if hasattr(st, "switch_page"):
            st.switch_page("pages/debitos.py")
        else:
            st.session_state["menu"] = "Débitos"; _do_rerun(); return
    if st.sidebar.button("Configurações", width='stretch'):
        if hasattr(st, "switch_page"):
            st.switch_page("pages/configuracoes.py")
        else:
            st.session_state["menu"] = "Configurações"; _do_rerun(); return
    if st.sidebar.button("Logout", type="primary", width='stretch'):
        st.session_state["show_logout_confirm"] = True

    # Logout confirmation popup (uses st.dialog when available)
    if st.session_state.get("show_logout_confirm"):
        dialog_decorator = getattr(st, "dialog", None)
        if callable(dialog_decorator):
            @dialog_decorator("Confirmar logout")
            def _logout_dialog():
                st.write("Deseja sair da sessão?")
                spacer_left, c1, c2, spacer_right = st.columns([1, 3, 3, 1])
                with c1:
                    if st.button("Cancelar", width='stretch'):
                        st.session_state["show_logout_confirm"] = False
                        _do_rerun()
                with c2:
                    if st.button("Sair", type="primary", width='stretch'):
                        logout()
                        st.session_state["show_logout_confirm"] = False
                        if hasattr(st, "switch_page"):
                            st.switch_page("pages/login.py")
                        else:
                            st.session_state["menu"] = "Dashboard"
                            _do_rerun()

            _logout_dialog()
        else:
            # Inline fallback if dialog API is unavailable
            st.warning("Deseja sair da sessão?")
            spacer_left, c1, c2, spacer_right = st.columns([1, 3, 3, 1])
            with c1:
                if st.button("Cancelar", width='stretch'):
                    st.session_state["show_logout_confirm"] = False
                    _do_rerun()
            with c2:
                if st.button("Sair", type="primary", width='stretch'):
                    logout()
                    st.session_state["show_logout_confirm"] = False
                    if hasattr(st, "switch_page"):
                        st.switch_page("pages/login.py")
                    else:
                        st.session_state["menu"] = "Dashboard"
                        _do_rerun()
