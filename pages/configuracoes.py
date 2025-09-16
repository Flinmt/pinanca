from __future__ import annotations
import uuid
from pathlib import Path
import pandas as pd
import streamlit as st

from core.session import current_user
from ui.nav import render_sidebar

from services.debt_origins import DebtOrigin
from repository.debt_origins import DebtOriginRepository
from services.responsibles import Responsible
from services.categories import Category
from repository.responsibles import ResponsibleRepository
from repository.categories import CategoryRepository
from repository.users import UserRepository


# -------------------- util --------------------
def _do_rerun() -> None:
    fn = getattr(st, "rerun", None) or getattr(st, "experimental_rerun", None)
    if fn:
        fn()


PROFILE_DIR = Path("data/profile_images")


def _ensure_dirs() -> None:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)


def _save_profile_image(upload) -> str | None:
    if not upload:
        return None
    _ensure_dirs()
    suffix = "".join(Path(upload.name).suffixes) or ".png"
    filename = f"{uuid.uuid4().hex}{suffix}"
    dest = PROFILE_DIR / filename
    with open(dest, "wb") as f:
        f.write(upload.getbuffer())
    return str(dest)


def _load_origins(user_id: int):
    try:
        return DebtOriginRepository.list_by_user(user_id)
    except Exception as e:
        st.warning(f"Erro ao carregar origens: {e}")
        return []


def _load_responsibles(user_id: int):
    try:
        return ResponsibleRepository.list_by_user(user_id)
    except Exception as e:
        st.warning(f"Erro ao carregar responsáveis: {e}")
        return []


def _load_categories(user_id: int):
    try:
        return CategoryRepository.list_by_user(user_id)
    except Exception as e:
        st.warning(f"Erro ao carregar categorias: {e}")
        return []


def _df_from_models(items, id_fn, name_fn):
    return pd.DataFrame([{"id": id_fn(x), "nome": name_fn(x)} for x in items])


def _apply_updates(df_original: pd.DataFrame, df_editado: pd.DataFrame, update_fn):
    """Compara apenas a coluna 'nome' por id; ignora colunas extras como 'sel'."""
    alterados = 0
    base_map = {int(r["id"]): str(r["nome"] or "").strip() for _, r in df_original.iterrows()}
    for _, row in df_editado.iterrows():
        rid = int(row["id"])
        new_name = str(row.get("nome", "") or "").strip()
        if base_map.get(rid, "") != new_name:
            try:
                update_fn(rid, new_name or None)
                alterados += 1
            except Exception as e:
                st.error(f"Erro ao atualizar id={rid}: {e}")
    return alterados


def _apply_deletes(ids, delete_fn, label: str):
    removidos = 0
    for rid in ids:
        try:
            delete_fn(int(rid))
            removidos += 1
        except Exception as e:
            st.error(f"Erro ao remover id={rid}: {e}")
    if removidos:
        st.toast(f"{removidos} {label} removido(s)", icon="✅")


# -------------------- page --------------------
def render(user=None):
    user = user or current_user()
    if not user:
        if hasattr(st, "switch_page"):
            st.switch_page("pages/login.py")
        else:
            st.stop()

    render_sidebar(user)
    st.title("Configurações")

    # ---------- Imagem de Perfil ----------
    st.subheader("Imagem de Perfil")
    with st.form("profile_image_form", border=True):
        uploaded = st.file_uploader(
            "Envie sua imagem (PNG/JPG)",
            type=["png", "jpg", "jpeg", "webp"],
            accept_multiple_files=False,
        )
        if st.form_submit_button("Salvar imagem"):
            try:
                new_path = _save_profile_image(uploaded)
                if new_path:
                    user.set_profile_image(new_path)
                    UserRepository.update(user)
                    st.toast("Imagem atualizada!", icon="✅")
                    _do_rerun()
                else:
                    st.info("Nenhum arquivo selecionado.")
            except Exception as e:
                st.error(f"Falha ao salvar imagem: {e}")

    st.divider()

    # ======================================================================
    # ORIGENS
    # ======================================================================
    st.subheader("Origens de Dívida")

    # criar
    with st.form("origin_add_form", clear_on_submit=True, border=True):
        new_origin_name = st.text_input("Nova origem", placeholder="Ex.: Cartão de Crédito")
        if st.form_submit_button("Adicionar origem"):
            if new_origin_name.strip():
                try:
                    DebtOriginRepository.create(
                        DebtOrigin(user_id=user.get_id(), name=new_origin_name.strip())
                    )
                    st.toast("Origem adicionada!", icon="✅")
                    _do_rerun()
                except Exception as e:
                    st.error(f"Erro ao adicionar origem: {e}")
            else:
                st.info("Informe um nome.")

    origins = _load_origins(user.get_id())
    if origins:
        df_o = _df_from_models(origins, lambda x: x.get_id(), lambda x: x.get_name())
        df_o["sel"] = False  # coluna de seleção manual
        # Mover ID para o índice e ordenar colunas: seletor à esquerda, nome à direita
        df_o = df_o.set_index("id", drop=True)[["sel", "nome"]]
        st.caption("Edite a coluna **Nome**. Marque **Selecionar** para excluir em lote.")

        edited_o = st.data_editor(
            df_o,
            hide_index=True,
            width='stretch',
            column_config={
                "nome": st.column_config.TextColumn(
                    "Nome", required=True, help="Edite e clique em Salvar alterações"
                ),
                "sel": st.column_config.CheckboxColumn("Selecionar", width="small"),
            },
            num_rows="fixed",
            key="origins_editor",
        )

        # IDs selecionados vêm do índice
        selected_ids_o = (
            edited_o.index[edited_o["sel"] == True].astype(int).tolist()
            if not edited_o.empty else []
        )

        # feedback selecionados
        if selected_ids_o:
            name_map_o = {o.get_id(): (o.get_name() or "(sem nome)") for o in origins}
            preview_o = ", ".join(name_map_o.get(oid, str(oid)) for oid in selected_ids_o)
            st.caption(f"Selecionados ({len(selected_ids_o)}): {preview_o}")

        sp_l, center, sp_r = st.columns([1, 4, 1])
        with center:
            col1, col2 = st.columns(2)
        with col1:
            if st.button("Salvar alterações", type="primary", key="save_origins_btn", width='stretch'):
                def _update_origin(oid, new_name):
                    o = next(x for x in origins if x.get_id() == oid)
                    o.set_name(new_name)
                    DebtOriginRepository.update(o)

                # Converte de volta o índice 'id' para coluna para aplicar atualizações
                base_o = df_o.reset_index()[["id", "nome"]]
                edit_o = edited_o.reset_index()[["id", "nome"]]
                alterados = _apply_updates(base_o, edit_o, _update_origin)
                if alterados:
                    st.toast("Alterações salvas.", icon="✅")
                    _do_rerun()
        with col2:
            if st.button(
                f"Excluir selecionados ({len(selected_ids_o)})",
                disabled=len(selected_ids_o) == 0,
                key="del_origins_btn",
                width='stretch',
            ):
                st.session_state["confirm_delete_origin_ids"] = selected_ids_o
                _do_rerun()
    else:
        st.info("Nenhuma origem cadastrada.")

    # confirmação exclusão em lote de origens
    if st.session_state.get("confirm_delete_origin_ids"):
        ids = list(st.session_state.get("confirm_delete_origin_ids", []))
        dialog = getattr(st, "dialog", None)
        if callable(dialog):
            @dialog("Confirmar exclusão de origens")
            def _confirm_del_origins():
                st.write("Confirma a exclusão das origens selecionadas?")
                origins_all = _load_origins(user.get_id())
                if ids and origins_all:
                    name_map = {o.get_id(): (o.get_name() or "(sem nome)") for o in origins_all}
                    st.markdown("\n".join(f"- {name_map.get(i, str(i))}" for i in ids))
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Cancelar", width='stretch'):
                        st.session_state["confirm_delete_origin_ids"] = []
                        _do_rerun()
                with c2:
                    if st.button("Excluir", type="primary", width='stretch'):
                        _apply_deletes(ids, DebtOriginRepository.delete, "origem(ns)")
                        st.session_state["confirm_delete_origin_ids"] = []
                        _do_rerun()
            _confirm_del_origins()
        else:
            st.warning("Confirma a exclusão das origens selecionadas?")
            origins_all = _load_origins(user.get_id())
            if ids and origins_all:
                name_map = {o.get_id(): (o.get_name() or "(sem nome)") for o in origins_all}
                st.markdown("\n".join(f"- {name_map.get(i, str(i))}" for i in ids))
            c1, c2 = st.columns(2)
            if c1.button("Cancelar"):
                st.session_state["confirm_delete_origin_ids"] = []
                _do_rerun()
            if c2.button("Excluir", type="primary"):
                _apply_deletes(ids, DebtOriginRepository.delete, "origem(ns)")
                st.session_state["confirm_delete_origin_ids"] = []
                _do_rerun()

    st.divider()

    # ======================================================================
    # CATEGORIAS
    # ======================================================================
    st.subheader("Categorias")

    with st.form("category_add_form", clear_on_submit=True, border=True):
        new_cat_name = st.text_input("Nova categoria", placeholder="Ex.: Alimentação")
        if st.form_submit_button("Adicionar categoria"):
            if new_cat_name.strip():
                try:
                    CategoryRepository.create(
                        Category(user_id=user.get_id(), name=new_cat_name.strip())
                    )
                    st.toast("Categoria adicionada!", icon="✅")
                    _do_rerun()
                except Exception as e:
                    st.error(f"Erro ao adicionar categoria: {e}")
            else:
                st.info("Informe um nome.")

    categories = _load_categories(user.get_id())
    if categories:
        df_c = _df_from_models(categories, lambda x: x.get_id(), lambda x: x.get_name() or "")
        df_c["sel"] = False
        df_c = df_c.set_index("id", drop=True)[["sel", "nome"]]
        st.caption("Edite a coluna **Nome**. Marque **Selecionar** para excluir em lote.")

        edited_c = st.data_editor(
            df_c,
            hide_index=True,
            width='stretch',
            column_config={
                "nome": st.column_config.TextColumn(
                    "Nome", required=True, help="Edite e clique em Salvar alterações"
                ),
                "sel": st.column_config.CheckboxColumn("Selecionar", width="small"),
            },
            num_rows="fixed",
            key="categories_editor",
        )

        selected_ids_c = (
            edited_c.index[edited_c["sel"] == True].astype(int).tolist()
            if not edited_c.empty else []
        )

        if selected_ids_c:
            name_map_c = {c.get_id(): (c.get_name() or "(sem nome)") for c in categories}
            preview_c = ", ".join(name_map_c.get(cid, str(cid)) for cid in selected_ids_c)
            st.caption(f"Selecionados ({len(selected_ids_c)}): {preview_c}")

        sp_lc, centerc, sp_rc = st.columns([1, 4, 1])
        with centerc:
            ccol1, ccol2 = st.columns(2)
        with ccol1:
            if st.button("Salvar alterações", type="primary", key="save_cats_btn", width='stretch'):
                def _update_cat(cid, new_name):
                    c = next(x for x in categories if x.get_id() == cid)
                    c.set_name(new_name)
                    CategoryRepository.update(c)

                base_c = df_c.reset_index()[["id", "nome"]]
                edit_c = edited_c.reset_index()[["id", "nome"]]
                alterados = _apply_updates(base_c, edit_c, _update_cat)
                if alterados:
                    st.toast("Alterações salvas.", icon="✅")
                    _do_rerun()
        with ccol2:
            if st.button(
                f"Excluir selecionados ({len(selected_ids_c)})",
                disabled=len(selected_ids_c) == 0,
                key="del_cats_btn",
                width='stretch',
            ):
                st.session_state["confirm_delete_cat_ids"] = selected_ids_c
                _do_rerun()
    else:
        st.info("Nenhuma categoria cadastrada.")

    if st.session_state.get("confirm_delete_cat_ids"):
        ids = list(st.session_state.get("confirm_delete_cat_ids", []))
        dialog = getattr(st, "dialog", None)
        if callable(dialog):
            @dialog("Confirmar exclusão de categorias")
            def _confirm_del_cats():
                st.write("Confirma a exclusão das categorias selecionadas?")
                cats_all = _load_categories(user.get_id())
                if ids and cats_all:
                    name_map = {c.get_id(): (c.get_name() or "(sem nome)") for c in cats_all}
                    st.markdown("\n".join(f"- {name_map.get(i, str(i))}" for i in ids))
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Cancelar", width='stretch'):
                        st.session_state["confirm_delete_cat_ids"] = []
                        _do_rerun()
                with col2:
                    if st.button("Excluir", type="primary", width='stretch'):
                        _apply_deletes(ids, CategoryRepository.delete, "categoria(s)")
                        st.session_state["confirm_delete_cat_ids"] = []
                        _do_rerun()
            _confirm_del_cats()
        else:
            st.warning("Confirma a exclusão das categorias selecionadas?")
            cats_all = _load_categories(user.get_id())
            if ids and cats_all:
                name_map = {c.get_id(): (c.get_name() or "(sem nome)") for c in cats_all}
                st.markdown("\n".join(f"- {name_map.get(i, str(i))}" for i in ids))
            col1, col2 = st.columns(2)
            if col1.button("Cancelar"):
                st.session_state["confirm_delete_cat_ids"] = []
                _do_rerun()
            if col2.button("Excluir", type="primary"):
                _apply_deletes(ids, CategoryRepository.delete, "categoria(s)")
                st.session_state["confirm_delete_cat_ids"] = []
                _do_rerun()

    st.divider()

    # ======================================================================
    # RESPONSÁVEIS
    # ======================================================================
    st.subheader("Responsáveis")

    # criar
    with st.form("resp_add_form", clear_on_submit=True, border=True):
        new_resp_name = st.text_input("Novo responsável", placeholder="Ex.: João")
        if st.form_submit_button("Adicionar responsável"):
            if new_resp_name.strip():
                try:
                    ResponsibleRepository.create(
                        Responsible(user_id=user.get_id(), name=new_resp_name.strip())
                    )
                    st.toast("Responsável adicionado!", icon="✅")
                    _do_rerun()
                except Exception as e:
                    st.error(f"Erro ao adicionar responsável: {e}")
            else:
                st.info("Informe um nome.")

    responsibles = _load_responsibles(user.get_id())
    if responsibles:
        df_r = _df_from_models(responsibles, lambda x: x.get_id(), lambda x: x.get_name() or "")
        df_r["sel"] = False
        # Mover ID para o índice e ordenar colunas: seletor à esquerda, nome à direita
        df_r = df_r.set_index("id", drop=True)[["sel", "nome"]]
        st.caption("Edite a coluna **Nome**. Marque **Selecionar** para excluir em lote.")

        edited_r = st.data_editor(
            df_r,
            hide_index=True,
            width='stretch',
            column_config={
                "nome": st.column_config.TextColumn(
                    "Nome", required=False, help="Pode ficar em branco"
                ),
                "sel": st.column_config.CheckboxColumn("Selecionar", width="small"),
            },
            num_rows="fixed",
            key="responsibles_editor",
        )

        selected_ids_r = (
            edited_r.index[edited_r["sel"] == True].astype(int).tolist()
            if not edited_r.empty else []
        )

        if selected_ids_r:
            name_map_r = {r.get_id(): (r.get_name() or "(sem nome)") for r in responsibles}
            preview_r = ", ".join(name_map_r.get(rid, str(rid)) for rid in selected_ids_r)
            st.caption(f"Selecionados ({len(selected_ids_r)}): {preview_r}")

        sp_l2, center2, sp_r2 = st.columns([1, 4, 1])
        with center2:
            rcol1, rcol2 = st.columns(2)
        with rcol1:
            if st.button("Salvar alterações", type="primary", key="save_resps_btn", width='stretch'):
                def _update_resp(rid, new_name):
                    r = next(x for x in responsibles if x.get_id() == rid)
                    r.set_name((new_name or "").strip() or None)
                    ResponsibleRepository.update(r)

                base_r = df_r.reset_index()[["id", "nome"]]
                edit_r = edited_r.reset_index()[["id", "nome"]]
                alterados = _apply_updates(base_r, edit_r, _update_resp)
                if alterados:
                    st.toast("Alterações salvas.", icon="✅")
                    _do_rerun()
        with rcol2:
            if st.button(
                f"Excluir selecionados ({len(selected_ids_r)})",
                disabled=len(selected_ids_r) == 0,
                key="del_resps_btn",
                width='stretch',
            ):
                st.session_state["confirm_delete_resp_ids"] = selected_ids_r
                _do_rerun()
    else:
        st.info("Nenhum responsável cadastrado.")

    # confirmação exclusão em lote de responsáveis
    if st.session_state.get("confirm_delete_resp_ids"):
        ids = list(st.session_state.get("confirm_delete_resp_ids", []))
        dialog = getattr(st, "dialog", None)
        if callable(dialog):
            @dialog("Confirmar exclusão de responsáveis")
            def _confirm_del_resps():
                st.write("Confirma a exclusão dos responsáveis selecionados?")
                resps_all = _load_responsibles(user.get_id())
                if ids and resps_all:
                    name_map = {r.get_id(): (r.get_name() or "(sem nome)") for r in resps_all}
                    st.markdown("\n".join(f"- {name_map.get(i, str(i))}" for i in ids))
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Cancelar", width='stretch'):
                        st.session_state["confirm_delete_resp_ids"] = []
                        _do_rerun()
                with c2:
                    if st.button("Excluir", type="primary", width='stretch'):
                        _apply_deletes(ids, ResponsibleRepository.delete, "responsável(is)")
                        st.session_state["confirm_delete_resp_ids"] = []
                        _do_rerun()
            _confirm_del_resps()
        else:
            st.warning("Confirma a exclusão dos responsáveis selecionados?")
            resps_all = _load_responsibles(user.get_id())
            if ids and resps_all:
                name_map = {r.get_id(): (r.get_name() or "(sem nome)") for r in resps_all}
                st.markdown("\n".join(f"- {name_map.get(i, str(i))}" for i in ids))
            c1, c2 = st.columns(2)
            if c1.button("Cancelar"):
                st.session_state["confirm_delete_resp_ids"] = []
                _do_rerun()
            if c2.button("Excluir", type="primary"):
                _apply_deletes(ids, ResponsibleRepository.delete, "responsável(is)")
                st.session_state["confirm_delete_resp_ids"] = []
                _do_rerun()


# Auto-render
render()
