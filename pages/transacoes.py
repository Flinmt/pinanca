from __future__ import annotations
import streamlit as st
import pandas as pd
from datetime import date, datetime, time, timezone

from core.session import current_user
from ui.nav import render_sidebar

from services.transactions import Transaction
from repository.transactions import TransactionRepository


def _do_rerun() -> None:
    fn = getattr(st, "rerun", None) or getattr(st, "experimental_rerun", None)
    if fn:
        fn()


def _df_from_fixed(txs):
    data = []
    for t in txs:
        data.append(
            {
                "id": t.get_id(),
                "sel": False,
                "tipo": "Entrada" if (t.get_type() or "income") == "income" else "Saída",
                "descricao": t.get_description() or "",
                "valor": float(t.get_amount() or 0.0),
                "periodicidade": t.get_periodicity() or "none",
            }
        )
    return pd.DataFrame(data)


def _df_from_one_off(txs):
    data = []
    for t in txs:
        occurred = t.get_occurred_at()
        d = occurred.date() if isinstance(occurred, datetime) else occurred
        data.append(
            {
                "id": t.get_id(),
                "sel": False,
                "tipo": "Entrada" if (t.get_type() or "income") == "income" else "Saída",
                "descricao": t.get_description() or "",
                "valor": float(t.get_amount() or 0.0),
                "data": d or date.today(),
            }
        )
    return pd.DataFrame(data)


def render(user=None):
    user = user or current_user()
    if not user:
        if hasattr(st, "switch_page"):
            st.switch_page("pages/login.py")
        else:
            st.stop()

    render_sidebar(user)
    st.title("Transações")

    # ============================== Seções de listagem/edição =============================
    def _section_fixed_unified():
        st.subheader("Transações fixas")
        txs = TransactionRepository.list_by_filters(user.get_id(), fixed=True, limit=1000)
        if not txs:
            st.info("Nenhuma transação fixa cadastrada.")
            return

        df = _df_from_fixed(txs)
        df = df.set_index("id", drop=True)[["sel", "tipo", "descricao", "valor", "periodicidade"]]
        st.caption("Edite os campos e salve. Marque Selecionar para excluir em lote.")

        edited = st.data_editor(
            df,
            hide_index=True,
            width='stretch',
            column_config={
                "sel": st.column_config.CheckboxColumn("Selecionar", width="small"),
                "tipo": st.column_config.SelectboxColumn("Tipo", options=["Entrada", "Saída"], default="Entrada"),
                "descricao": st.column_config.TextColumn("Descrição", required=False),
                "valor": st.column_config.NumberColumn("Valor", min_value=0.01, step=0.01, format="%.2f"),
                "periodicidade": st.column_config.SelectboxColumn(
                    "Periodicidade", options=["monthly", "weekly", "yearly"], default="monthly"
                ),
            },
            num_rows="fixed",
            key="fixed_all_editor",
        )

        selected_ids = (
            edited.index[edited["sel"] == True].astype(int).tolist()
            if not edited.empty else []
        )

        if selected_ids:
            name_map = {t.get_id(): (t.get_description() or "(sem descrição)") for t in txs}
            preview = ", ".join(name_map.get(tid, str(tid)) for t in selected_ids)
            st.caption(f"Selecionados ({len(selected_ids)}): {preview}")

        sp_l, center, sp_r = st.columns([1, 4, 1])
        with center:
            c1, c2 = st.columns(2)
        with c1:
            if st.button("Salvar alterações", type="primary", key="save_fixed_all", width='stretch'):
                altered = 0
                base = df.reset_index()[["id", "tipo", "descricao", "valor", "periodicidade"]]
                curr = edited.reset_index()[["id", "tipo", "descricao", "valor", "periodicidade"]]
                base = base.fillna({"descricao": "", "valor": 0.0, "periodicidade": "monthly"})
                curr = curr.fillna({"descricao": "", "valor": 0.0, "periodicidade": "monthly"})
                for _, row in curr.iterrows():
                    orig = base.loc[base["id"] == row["id"]].iloc[0]
                    changed = (
                        str(orig["tipo"]) != str(row["tipo"]) or
                        str(orig["descricao"]).strip() != str(row["descricao"]).strip()
                        or float(orig["valor"]) != float(row["valor"]) or
                        str(orig["periodicidade"]) != str(row["periodicidade"]) 
                    )
                    if changed:
                        try:
                            tx = next(x for x in txs if x.get_id() == int(row["id"]))
                            tx.set_type("income" if str(row["tipo"]) == "Entrada" else "expense")
                            tx.set_description((str(row["descricao"]).strip() or None))
                            tx.set_amount(float(row["valor"]))
                            tx.set_periodicity(str(row["periodicidade"]))
                            TransactionRepository.update(tx)
                            altered += 1
                        except Exception as e:
                            st.error(f"Erro ao atualizar id={row['id']}: {e}")
                if altered:
                    st.toast(f"{altered} alteração(ões) salva(s)", icon="✅")
                    _do_rerun()
        with c2:
            if st.button(
                f"Excluir selecionados ({len(selected_ids)})",
                disabled=len(selected_ids) == 0,
                key="del_fixed_all",
                width='stretch',
            ):
                st.session_state["confirm_delete_fixed_all_ids"] = selected_ids
                _do_rerun()

        confirm_key = "confirm_delete_fixed_all_ids"
        if st.session_state.get(confirm_key):
            ids = list(st.session_state.get(confirm_key, []))
            dialog = getattr(st, "dialog", None)
            if callable(dialog):
                @dialog("Confirmar exclusão")
                def _confirm_delete_dialog():
                    st.write("Confirma a exclusão das transações selecionadas?")
                    if ids:
                        name_map = {t.get_id(): (t.get_description() or "(sem descrição)") for t in txs}
                        st.markdown("\n".join(f"- {name_map.get(i, str(i))}" for i in ids))
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("Cancelar", width='stretch'):
                            st.session_state[confirm_key] = []
                            _do_rerun()
                    with b2:
                        if st.button("Excluir", type="primary", width='stretch'):
                            removed = 0
                            for tid in ids:
                                try:
                                    TransactionRepository.delete(int(tid))
                                    removed += 1
                                except Exception as e:
                                    st.error(f"Erro ao remover id={tid}: {e}")
                            st.session_state[confirm_key] = []
                            st.toast(f"{removed} transação(ões) removida(s)", icon="✅")
                            _do_rerun()
                _confirm_delete_dialog()
            else:
                st.warning("Confirma a exclusão das transações selecionadas?")
                if ids:
                    name_map = {t.get_id(): (t.get_description() or "(sem descrição)") for t in txs}
                    st.markdown("\n".join(f"- {name_map.get(i, str(i))}" for i in ids))
                b1, b2 = st.columns(2)
                if b1.button("Cancelar"):
                    st.session_state[confirm_key] = []
                    _do_rerun()
                if b2.button("Excluir", type="primary"):
                    removed = 0
                    for tid in ids:
                        try:
                            TransactionRepository.delete(int(tid))
                            removed += 1
                        except Exception as e:
                            st.error(f"Erro ao remover id={tid}: {e}")
                    st.session_state[confirm_key] = []
                    st.toast(f"{removed} transação(ões) removida(s)", icon="✅")
                    _do_rerun()

    def _section_one_off_unified():
        st.subheader("Transações avulsas")
        txs = TransactionRepository.list_by_filters(user.get_id(), fixed=False, limit=1000)
        if not txs:
            st.info("Nenhuma transação avulsa cadastrada.")
            return

        df = _df_from_one_off(txs)
        df = df.set_index("id", drop=True)[["sel", "tipo", "descricao", "valor", "data"]]
        st.caption("Edite os campos e salve. Marque Selecionar para excluir em lote.")

        edited = st.data_editor(
            df,
            hide_index=True,
            width='stretch',
            column_config={
                "sel": st.column_config.CheckboxColumn("Selecionar", width="small"),
                "tipo": st.column_config.SelectboxColumn("Tipo", options=["Entrada", "Saída"], default="Entrada"),
                "descricao": st.column_config.TextColumn("Descrição", required=False),
                "valor": st.column_config.NumberColumn("Valor", min_value=0.01, step=0.01, format="%.2f"),
                "data": st.column_config.DateColumn("Data"),
            },
            num_rows="fixed",
            key="oneoff_all_editor",
        )

        selected_ids = (
            edited.index[edited["sel"] == True].astype(int).tolist()
            if not edited.empty else []
        )

        if selected_ids:
            name_map = {t.get_id(): (t.get_description() or "(sem descrição)") for t in txs}
            preview = ", ".join(name_map.get(tid, str(tid)) for t in selected_ids)
            st.caption(f"Selecionados ({len(selected_ids)}): {preview}")

        sp_l, center, sp_r = st.columns([1, 4, 1])
        with center:
            c1, c2 = st.columns(2)
        with c1:
            if st.button("Salvar alterações", type="primary", key="save_oneoff_all", width='stretch'):
                altered = 0
                base = df.reset_index()[["id", "tipo", "descricao", "valor", "data"]]
                curr = edited.reset_index()[["id", "tipo", "descricao", "valor", "data"]]
                base = base.fillna({"descricao": "", "valor": 0.0})
                curr = curr.fillna({"descricao": "", "valor": 0.0})
                for _, row in curr.iterrows():
                    orig = base.loc[base["id"] == row["id"]].iloc[0]
                    changed = (
                        str(orig["tipo"]) != str(row["tipo"]) or
                        str(orig["descricao"]).strip() != str(row["descricao"]).strip() or
                        float(orig["valor"]) != float(row["valor"]) or
                        (orig["data"] != row["data"]) 
                    )
                    if changed:
                        try:
                            tx = next(x for x in txs if x.get_id() == int(row["id"]))
                            tx.set_type("income" if str(row["tipo"]) == "Entrada" else "expense")
                            tx.set_description((str(row["descricao"]).strip() or None))
                            tx.set_amount(float(row["valor"]))
                            # Converter date -> datetime na virada do dia (UTC)
                            rd = row["data"]
                            if isinstance(rd, date):
                                occ_dt = datetime.combine(rd, time(0, 0, 0, tzinfo=timezone.utc))
                                tx.set_occurred_at(occ_dt)
                            TransactionRepository.update(tx)
                            altered += 1
                        except Exception as e:
                            st.error(f"Erro ao atualizar id={row['id']}: {e}")
                if altered:
                    st.toast(f"{altered} alteração(ões) salva(s)", icon="✅")
                    _do_rerun()
        with c2:
            if st.button(
                f"Excluir selecionados ({len(selected_ids)})",
                disabled=len(selected_ids) == 0,
                key="del_oneoff_all",
                width='stretch',
            ):
                st.session_state["confirm_delete_oneoff_all_ids"] = selected_ids
                _do_rerun()

        confirm_key = "confirm_delete_oneoff_all_ids"
        if st.session_state.get(confirm_key):
            ids = list(st.session_state.get(confirm_key, []))
            dialog = getattr(st, "dialog", None)
            if callable(dialog):
                @dialog("Confirmar exclusão")
                def _confirm_delete_dialog():
                    st.write("Confirma a exclusão das transações selecionadas?")
                    if ids:
                        name_map = {t.get_id(): (t.get_description() or "(sem descrição)") for t in txs}
                        st.markdown("\n".join(f"- {name_map.get(i, str(i))}" for i in ids))
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("Cancelar", width='stretch'):
                            st.session_state[confirm_key] = []
                            _do_rerun()
                    with b2:
                        if st.button("Excluir", type="primary", width='stretch'):
                            removed = 0
                            for tid in ids:
                                try:
                                    TransactionRepository.delete(int(tid))
                                    removed += 1
                                except Exception as e:
                                    st.error(f"Erro ao remover id={tid}: {e}")
                            st.session_state[confirm_key] = []
                            st.toast(f"{removed} transação(ões) removida(s)", icon="✅")
                            _do_rerun()
                _confirm_delete_dialog()
            else:
                st.warning("Confirma a exclusão das transações selecionadas?")
                if ids:
                    name_map = {t.get_id(): (t.get_description() or "(sem descrição)") for t in txs}
                    st.markdown("\n".join(f"- {name_map.get(i, str(i))}" for i in ids))
                b1, b2 = st.columns(2)
                if b1.button("Cancelar"):
                    st.session_state[confirm_key] = []
                    _do_rerun()
                if b2.button("Excluir", type="primary"):
                    removed = 0
                    for tid in ids:
                        try:
                            TransactionRepository.delete(int(tid))
                            removed += 1
                        except Exception as e:
                            st.error(f"Erro ao remover id={tid}: {e}")
                    st.session_state[confirm_key] = []
                    st.toast(f"{removed} transação(ões) removida(s)", icon="✅")
                    _do_rerun()

    # ============================== Cadastro de fixas ===============================
    st.subheader("Entradas/Saídas fixas")

    # Seletor de categoria removido

    with st.form("fixed_tx_form", border=True, clear_on_submit=True):
        c1, c2 = st.columns([1, 2])
        with c1:
            tipo_label = st.selectbox("Tipo", options=["Entrada", "Saída"], index=0)
            periodicidade = st.selectbox("Periodicidade", options=["monthly", "weekly", "yearly"], index=0)
        with c2:
            descricao = st.text_input("Descrição", placeholder="Ex.: Salário, Aluguel")
            valor = st.number_input("Valor", min_value=0.00, step=0.01, format="%.2f")

        if st.form_submit_button("Cadastrar", type="primary"):
            try:
                # Sem categoria (seletor removido)
                cat_id = None

                tipo = "income" if tipo_label == "Entrada" else "expense"
                model = Transaction(
                    user_id=user.get_id(),
                    category_id=cat_id,
                    amount=float(valor),
                    type=tipo,
                    fixed=True,
                    periodicity=periodicidade,
                    description=(descricao or "").strip() or None,
                )
                TransactionRepository.create(model)
                st.toast("Transação fixa cadastrada!", icon="✅")
                _do_rerun()
            except Exception as e:
                st.error(f"Erro ao cadastrar: {e}")

    # Renderiza tabela de fixas logo abaixo do cadastro
    _section_fixed_unified()
    st.divider()

    # ============================== Cadastro de avulsas ===============================
    st.subheader("Entradas/Saídas avulsas")
    with st.form("one_off_tx_form", border=True, clear_on_submit=True):
        c1, c2 = st.columns([1, 2])
        with c1:
            tipo_label2 = st.selectbox("Tipo", options=["Entrada", "Saída"], index=0, key="oneoff_tipo")
            data_ocorr = st.date_input("Data", value=date.today(), key="oneoff_data")
        with c2:
            descricao2 = st.text_input("Descrição", placeholder="Ex.: Bônus, Compra pontual", key="oneoff_desc")
            valor2 = st.number_input("Valor", min_value=0.00, step=0.01, format="%.2f", key="oneoff_val")
        if st.form_submit_button("Cadastrar", type="primary"):
            try:
                tipo2 = "income" if tipo_label2 == "Entrada" else "expense"
                occ_dt = datetime.combine(data_ocorr, time(0, 0, 0, tzinfo=timezone.utc))
                model2 = Transaction(
                    user_id=user.get_id(),
                    category_id=None,
                    amount=float(valor2),
                    type=tipo2,
                    fixed=False,
                    periodicity="none",
                    occurred_at=occ_dt,
                    description=(descricao2 or "").strip() or None,
                )
                TransactionRepository.create(model2)
                st.toast("Transação avulsa cadastrada!", icon="✅")
                _do_rerun()
            except Exception as e:
                st.error(f"Erro ao cadastrar: {e}")

    # Renderiza tabela de avulsas logo abaixo do cadastro
    _section_one_off_unified()

    # ============================== Visualização/edição (unificada) =============================
    def _section_fixed_unified():
        st.subheader("Transações fixas")
        txs = TransactionRepository.list_by_filters(user.get_id(), fixed=True, limit=1000)
        if not txs:
            st.info("Nenhuma transação fixa cadastrada.")
            return

        df = _df_from_fixed(txs)
        df = df.set_index("id", drop=True)[["sel", "tipo", "descricao", "valor", "periodicidade"]]
        st.caption("Edite os campos e salve. Marque Selecionar para excluir em lote.")

        edited = st.data_editor(
            df,
            hide_index=True,
            width='stretch',
            column_config={
                "sel": st.column_config.CheckboxColumn("Selecionar", width="small"),
                "tipo": st.column_config.SelectboxColumn("Tipo", options=["Entrada", "Saída"], default="Entrada"),
                "descricao": st.column_config.TextColumn("Descrição", required=False),
                "valor": st.column_config.NumberColumn("Valor", min_value=0.01, step=0.01, format="%.2f"),
                "periodicidade": st.column_config.SelectboxColumn(
                    "Periodicidade", options=["monthly", "weekly", "yearly"], default="monthly"
                ),
            },
            num_rows="fixed",
            key="fixed_all_editor",
        )

        selected_ids = (
            edited.index[edited["sel"] == True].astype(int).tolist()
            if not edited.empty else []
        )

        if selected_ids:
            name_map = {t.get_id(): (t.get_description() or "(sem descrição)") for t in txs}
            preview = ", ".join(name_map.get(tid, str(tid)) for tid in selected_ids)
            st.caption(f"Selecionados ({len(selected_ids)}): {preview}")

        sp_l, center, sp_r = st.columns([1, 4, 1])
        with center:
            c1, c2 = st.columns(2)
        with c1:
            if st.button("Salvar alterações", type="primary", key="save_fixed_all", width='stretch'):
                altered = 0
                base = df.reset_index()[["id", "tipo", "descricao", "valor", "periodicidade"]]
                curr = edited.reset_index()[["id", "tipo", "descricao", "valor", "periodicidade"]]
                base = base.fillna({"descricao": "", "valor": 0.0, "periodicidade": "monthly"})
                curr = curr.fillna({"descricao": "", "valor": 0.0, "periodicidade": "monthly"})
                for _, row in curr.iterrows():
                    orig = base.loc[base["id"] == row["id"]].iloc[0]
                    changed = (
                        str(orig["tipo"]) != str(row["tipo"]) or
                        str(orig["descricao"]).strip() != str(row["descricao"]).strip()
                        or float(orig["valor"]) != float(row["valor"])
                        or str(orig["periodicidade"]) != str(row["periodicidade"]) 
                    )
                    if changed:
                        try:
                            tx = next(x for x in txs if x.get_id() == int(row["id"]))
                            # Tipo
                            tx.set_type("income" if str(row["tipo"]) == "Entrada" else "expense")
                            tx.set_description((str(row["descricao"]).strip() or None))
                            tx.set_amount(float(row["valor"]))
                            tx.set_periodicity(str(row["periodicidade"]))
                            # next_execution não é editado na tabela
                            TransactionRepository.update(tx)
                            altered += 1
                        except Exception as e:
                            st.error(f"Erro ao atualizar id={row['id']}: {e}")
                if altered:
                    st.toast(f"{altered} alteração(ões) salva(s)", icon="✅")
                    _do_rerun()
        with c2:
            if st.button(
                f"Excluir selecionados ({len(selected_ids)})",
                disabled=len(selected_ids) == 0,
                key="del_fixed_all",
                width='stretch',
            ):
                st.session_state["confirm_delete_fixed_all_ids"] = selected_ids
                _do_rerun()

        confirm_key = "confirm_delete_fixed_all_ids"
        if st.session_state.get(confirm_key):
            ids = list(st.session_state.get(confirm_key, []))
            dialog = getattr(st, "dialog", None)
            if callable(dialog):
                @dialog("Confirmar exclusão")
                def _confirm_delete_dialog():
                    st.write("Confirma a exclusão das transações selecionadas?")
                    if ids:
                        name_map = {t.get_id(): (t.get_description() or "(sem descrição)") for t in txs}
                        st.markdown("\n".join(f"- {name_map.get(i, str(i))}" for i in ids))
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("Cancelar", width='stretch'):
                            st.session_state[confirm_key] = []
                            _do_rerun()
                    with b2:
                        if st.button("Excluir", type="primary", width='stretch'):
                            removed = 0
                            for tid in ids:
                                try:
                                    TransactionRepository.delete(int(tid))
                                    removed += 1
                                except Exception as e:
                                    st.error(f"Erro ao remover id={tid}: {e}")
                            st.session_state[confirm_key] = []
                            st.toast(f"{removed} transação(ões) removida(s)", icon="✅")
                            _do_rerun()
                _confirm_delete_dialog()
            else:
                st.warning("Confirma a exclusão das transações selecionadas?")
                if ids:
                    name_map = {t.get_id(): (t.get_description() or "(sem descrição)") for t in txs}
                    st.markdown("\n".join(f"- {name_map.get(i, str(i))}" for i in ids))
                b1, b2 = st.columns(2)
                if b1.button("Cancelar"):
                    st.session_state[confirm_key] = []
                    _do_rerun()
                if b2.button("Excluir", type="primary"):
                    removed = 0
                    for tid in ids:
                        try:
                            TransactionRepository.delete(int(tid))
                            removed += 1
                        except Exception as e:
                            st.error(f"Erro ao remover id={tid}: {e}")
                    st.session_state[confirm_key] = []
                    st.toast(f"{removed} transação(ões) removida(s)", icon="✅")
                    _do_rerun()

    # (movido) tabela de fixas é renderizada abaixo do cadastro
    # st.divider()

    # ============================== Visualização/edição (avulsas) =============================
    def _section_one_off_unified():
        st.subheader("Transações avulsas")
        txs = TransactionRepository.list_by_filters(user.get_id(), fixed=False, limit=1000)
        if not txs:
            st.info("Nenhuma transação avulsa cadastrada.")
            return

        df = _df_from_one_off(txs)
        df = df.set_index("id", drop=True)[["sel", "tipo", "descricao", "valor", "data"]]
        st.caption("Edite os campos e salve. Marque Selecionar para excluir em lote.")

        edited = st.data_editor(
            df,
            hide_index=True,
            width='stretch',
            column_config={
                "sel": st.column_config.CheckboxColumn("Selecionar", width="small"),
                "tipo": st.column_config.SelectboxColumn("Tipo", options=["Entrada", "Saída"], default="Entrada"),
                "descricao": st.column_config.TextColumn("Descrição", required=False),
                "valor": st.column_config.NumberColumn("Valor", min_value=0.01, step=0.01, format="%.2f"),
                "data": st.column_config.DateColumn("Data"),
            },
            num_rows="fixed",
            key="oneoff_all_editor",
        )

        selected_ids = (
            edited.index[edited["sel"] == True].astype(int).tolist()
            if not edited.empty else []
        )

        if selected_ids:
            name_map = {t.get_id(): (t.get_description() or "(sem descrição)") for t in txs}
            preview = ", ".join(name_map.get(tid, str(tid)) for tid in selected_ids)
            st.caption(f"Selecionados ({len(selected_ids)}): {preview}")

        sp_l, center, sp_r = st.columns([1, 4, 1])
        with center:
            c1, c2 = st.columns(2)
        with c1:
            if st.button("Salvar alterações", type="primary", key="save_oneoff_all", width='stretch'):
                altered = 0
                base = df.reset_index()[["id", "tipo", "descricao", "valor", "data"]]
                curr = edited.reset_index()[["id", "tipo", "descricao", "valor", "data"]]
                base = base.fillna({"descricao": "", "valor": 0.0})
                curr = curr.fillna({"descricao": "", "valor": 0.0})
                for _, row in curr.iterrows():
                    orig = base.loc[base["id"] == row["id"]].iloc[0]
                    changed = (
                        str(orig["tipo"]) != str(row["tipo"]) or
                        str(orig["descricao"]).strip() != str(row["descricao"]).strip() or
                        float(orig["valor"]) != float(row["valor"]) or
                        (orig["data"] != row["data"]) 
                    )
                    if changed:
                        try:
                            tx = next(x for x in txs if x.get_id() == int(row["id"]))
                            tx.set_type("income" if str(row["tipo"]) == "Entrada" else "expense")
                            tx.set_description((str(row["descricao"]).strip() or None))
                            tx.set_amount(float(row["valor"]))
                            # Converter date -> datetime na virada do dia (UTC)
                            rd = row["data"]
                            if isinstance(rd, date):
                                occ_dt = datetime.combine(rd, time(0, 0, 0, tzinfo=timezone.utc))
                                tx.set_occurred_at(occ_dt)
                            TransactionRepository.update(tx)
                            altered += 1
                        except Exception as e:
                            st.error(f"Erro ao atualizar id={row['id']}: {e}")
                if altered:
                    st.toast(f"{altered} alteração(ões) salva(s)", icon="✅")
                    _do_rerun()
        with c2:
            if st.button(
                f"Excluir selecionados ({len(selected_ids)})",
                disabled=len(selected_ids) == 0,
                key="del_oneoff_all",
                width='stretch',
            ):
                st.session_state["confirm_delete_oneoff_all_ids"] = selected_ids
                _do_rerun()

        confirm_key = "confirm_delete_oneoff_all_ids"
        if st.session_state.get(confirm_key):
            ids = list(st.session_state.get(confirm_key, []))
            dialog = getattr(st, "dialog", None)
            if callable(dialog):
                @dialog("Confirmar exclusão")
                def _confirm_delete_dialog():
                    st.write("Confirma a exclusão das transações selecionadas?")
                    if ids:
                        name_map = {t.get_id(): (t.get_description() or "(sem descrição)") for t in txs}
                        st.markdown("\n".join(f"- {name_map.get(i, str(i))}" for i in ids))
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("Cancelar", width='stretch'):
                            st.session_state[confirm_key] = []
                            _do_rerun()
                    with b2:
                        if st.button("Excluir", type="primary", width='stretch'):
                            removed = 0
                            for tid in ids:
                                try:
                                    TransactionRepository.delete(int(tid))
                                    removed += 1
                                except Exception as e:
                                    st.error(f"Erro ao remover id={tid}: {e}")
                            st.session_state[confirm_key] = []
                            st.toast(f"{removed} transação(ões) removida(s)", icon="✅")
                            _do_rerun()
                _confirm_delete_dialog()
            else:
                st.warning("Confirma a exclusão das transações selecionadas?")
                if ids:
                    name_map = {t.get_id(): (t.get_description() or "(sem descrição)") for t in txs}
                    st.markdown("\n".join(f"- {name_map.get(i, str(i))}" for i in ids))
                b1, b2 = st.columns(2)
                if b1.button("Cancelar"):
                    st.session_state[confirm_key] = []
                    _do_rerun()
                if b2.button("Excluir", type="primary"):
                    removed = 0
                    for tid in ids:
                        try:
                            TransactionRepository.delete(int(tid))
                            removed += 1
                        except Exception as e:
                            st.error(f"Erro ao remover id={tid}: {e}")
                    st.session_state[confirm_key] = []
                    st.toast(f"{removed} transação(ões) removida(s)", icon="✅")
                    _do_rerun()

    # (movido) tabela de avulsas é renderizada abaixo do cadastro


render()
