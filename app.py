from __future__ import annotations
import streamlit as st
from db.session import init_db
from core.session import current_user


def main() -> None:
    # Initialize database
    init_db()

    # Default route: Login if no session, else Dashboard
    user = current_user()
    if user:
        if hasattr(st, "switch_page"):
            st.switch_page("pages/dashboard.py")
        else:
            import pages.dashboard as dashboard
            dashboard.render(user)
    else:
        if hasattr(st, "switch_page"):
            st.switch_page("pages/login.py")
        else:
            import pages.login as login
            login.render()


if __name__ == "__main__":
    main()

