from __future__ import annotations
from datetime import date
import pandas as pd
import streamlit as st

from core.session import current_user
from ui.nav import render_sidebar

from services.debts import Debt
from repository.debts import DebtRepository
from repository.debt_origins import DebtOriginRepository
from repository.categories import CategoryRepository
from repository.responsibles import ResponsibleRepository

st.set_page_config(page_title="Débitos", layout="wide")

NONE_OPTION = "__none__"


def _do_rerun() -> None:
    fn = getattr(st, "rerun", None) or getattr(st, "experimental_rerun", None)
    if fn:
        fn()


def _load_origins(user_id: int):
    try:
        return DebtOriginRepository.list_by_user(user_id)
    except Exception as e:
        st.warning(f"Erro ao carregar origens: {e}")
        return []


def _load_categories(user_id: int):
    try:
        return CategoryRepository.list_by_user(user_id)
    except Exception as e:
        st.warning(f"Erro ao carregar categorias: {e}")
        return []


def _load_responsibles(user_id: int):
    try:
        return ResponsibleRepository.list_by_user(user_id)
    except Exception as e:
        st.warning(f"Erro ao carregar responsáveis: {e}")
        return []


def _option_map(items, label_fn, include_none: bool = False, none_label: str = "Sem"):
    mapping = {str(getattr(item, "get_id")()): label_fn(item) for item in items}
    if include_none:
        mapping[NONE_OPTION] = none_label
    return mapping


def _opt_to_str(value):
    return str(value) if value is not None else NONE_OPTION


def _str_to_opt(value):
    if value in (None, "", NONE_OPTION):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _df_from_debts(debts):
    rows = []
    for d in debts:
        rows.append(
            {
                "id": d.get_id(),
                "sel": False,
                "origem": _opt_to_str(d.get_origin_id()),
                "categoria": _opt_to_str(d.get_category_id()),
                "responsavel": _opt_to_str(d.get_responsible_id()),
                "descricao": d.get_description() or "",
                "data": d.get_debt_date() or date.today(),
                "valor_total": float(d.get_total_amount() or 0.0),
                "parcelas": int(d.get_installments() or 1),
                "ultima_parcela": d.get_last_installment_date(),
                "pago": bool(d.get_paid()),
                "notas": d.get_notes() or "",
            }
        )
    return pd.DataFrame(rows)


def render(user=None):
    user = user or current_user()
    if not user:
        if hasattr(st, "switch_page"):
            st.switch_page("pages/login.py")
        else:
            st.stop()

    render_sidebar(user)
    st.title("Débitos")

    origins = _load_origins(user.get_id())
    categories = _load_categories(user.get_id())
    responsibles = _load_responsibles(user.get_id())

    origin_map = _option_map(origins, lambda o: o.get_name() or f"Origem {o.get_id()}")
    category_map = _option_map(categories, lambda c: c.get_name() or f"Categoria {c.get_id()}", include_none=True, none_label="Sem categoria")
    responsible_map = _option_map(responsibles, lambda r: r.get_name() or f"Responsável {r.get_id()}", include_none=True, none_label="Sem responsável")

    st.subheader("Cadastrar débito")

    origin_options = [-1] + [o.get_id() for o in origins]
    origin_labels = {
        -1: "Selecione...",
        **{o.get_id(): origin_map.get(str(o.get_id()), f"Origem {o.get_id()}") for o in origins},
    }

    category_options = [None] + [c.get_id() for c in categories]
    category_labels = {
        None: "Sem categoria",
        **{c.get_id(): category_map.get(str(c.get_id()), f"Categoria {c.get_id()}") for c in categories},
    }

    responsible_options = [None] + [r.get_id() for r in responsibles]
    responsible_labels = {
        None: "Sem responsável",
        **{r.get_id(): responsible_map.get(str(r.get_id()), f"Responsável {r.get_id()}") for r in responsibles},
    }

    if st.session_state.pop("reset_debt_form", False):
        st.session_state["debt_form_date"] = date.today()
        st.session_state["debt_form_origin"] = -1
        st.session_state["debt_form_category"] = None
        st.session_state["debt_form_responsible"] = None
        st.session_state["debt_form_description"] = ""
        st.session_state["debt_form_total"] = 0.01
        st.session_state["debt_form_installments"] = 1
        st.session_state["debt_form_paid"] = False
        st.session_state["debt_form_notes"] = ""

    st.session_state.setdefault("debt_form_date", date.today())
    st.session_state.setdefault("debt_form_origin", -1)
    st.session_state.setdefault("debt_form_category", None)
    st.session_state.setdefault("debt_form_responsible", None)
    st.session_state.setdefault("debt_form_description", "")
    st.session_state.setdefault("debt_form_total", 0.01)
    st.session_state.setdefault("debt_form_installments", 1)
    st.session_state.setdefault("debt_form_paid", False)
    st.session_state.setdefault("debt_form_notes", "")

    if st.session_state["debt_form_origin"] not in origin_options:
        st.session_state["debt_form_origin"] = -1
    if st.session_state["debt_form_category"] not in category_options:
        st.session_state["debt_form_category"] = None
    if st.session_state["debt_form_responsible"] not in responsible_options:
        st.session_state["debt_form_responsible"] = None

    with st.container(border=True):
        left_col, right_col = st.columns(2)
        with left_col:
            debt_date = st.date_input(
                "Data",
                key="debt_form_date",
            )
            origin_choice = st.selectbox(
                "Origem",
                options=origin_options,
                format_func=lambda opt: origin_labels.get(opt, str(opt)),
                key="debt_form_origin",
            )
            category_choice = st.selectbox(
                "Categoria",
                options=category_options,
                format_func=lambda opt: category_labels.get(opt, str(opt)),
                key="debt_form_category",
            )
        with right_col:
            responsible_choice = st.selectbox(
                "Responsável",
                options=responsible_options,
                format_func=lambda opt: responsible_labels.get(opt, str(opt)),
                key="debt_form_responsible",
            )
            description = st.text_input(
                "Descrição",
                placeholder="Ex.: Parcelamento cartão",
                key="debt_form_description",
            )
            total_amount = st.number_input(
                "Valor total",
                min_value=0.01,
                step=0.01,
                format="%.2f",
                key="debt_form_total",
            )
        align_left, align_right = st.columns(2, vertical_alignment="bottom")
        with align_left:
            installments = st.number_input(
                "Parcelas",
                min_value=1,
                step=1,
                key="debt_form_installments",
            )
        with align_right:
            paid = st.checkbox(
                "Pago?",
                key="debt_form_paid",
            )
        notes = st.text_area(
            "Observações",
            placeholder="Detalhes adicionais",
            height=120,
            key="debt_form_notes",
        )

    submit_cols = st.columns([1, 2, 1])
    with submit_cols[1]:
        submit_clicked = st.button(
            "Cadastrar",
            type="primary",
            use_container_width=True,
            disabled=len(origin_options) <= 1,
            key="debt_form_submit",
        )

    if len(origin_options) <= 1:
        st.info("Cadastre uma origem nas configurações antes de registrar uma dívida.")

    if submit_clicked:
        if origin_choice == -1:
            st.info("Selecione uma origem.")
        else:
            try:
                model = Debt(
                    user_id=user.get_id(),
                    origin_id=origin_choice,
                    category_id=category_choice if category_choice is not None else None,
                    responsible_id=(responsible_choice if responsible_choice is not None else None),
                    debt_date=debt_date,
                    description=(description or "").strip() or None,
                    total_amount=float(total_amount),
                    installments=int(installments),
                    notes=(notes or "").strip() or None,
                    paid=bool(paid),
                )
                DebtRepository.create(model)
                st.toast("Dívida cadastrada!", icon="✅")
                st.session_state["reset_debt_form"] = True
                _do_rerun()
            except Exception as e:
                st.error(f"Erro ao cadastrar: {e}")

    st.divider()

    st.subheader("Débitos cadastrados")
    filter_cols = st.columns(4)
    with filter_cols[0]:
        status_choice = st.selectbox(
            "Status",
            options=["Todos", "Pendentes", "Quitados"],
            key="debts_filter_status",
        )
    origin_option_list = [(None, "Todas")] + [(o.get_id(), origin_map.get(str(o.get_id()), str(o.get_id()))) for o in origins]
    category_option_list = [(None, "Todas")] + [(c.get_id(), category_map.get(str(c.get_id()), str(c.get_id()))) for c in categories]
    responsible_option_list = [(None, "Todos")] + [(r.get_id(), responsible_map.get(str(r.get_id()), str(r.get_id()))) for r in responsibles]

    with filter_cols[1]:
        origin_filter = st.selectbox(
            "Origem",
            options=origin_option_list,
            format_func=lambda opt: opt[1],
            key="debts_filter_origin",
        )[0]
    with filter_cols[2]:
        category_filter = st.selectbox(
            "Categoria",
            options=category_option_list,
            format_func=lambda opt: opt[1],
            key="debts_filter_category",
        )[0]
    with filter_cols[3]:
        responsible_filter = st.selectbox(
            "Responsável",
            options=responsible_option_list,
            format_func=lambda opt: opt[1],
            key="debts_filter_responsible",
        )[0]

    paid_filter = None
    if status_choice == "Pendentes":
        paid_filter = False
    elif status_choice == "Quitados":
        paid_filter = True

    try:
        debts = DebtRepository.list_by_filters(
            user.get_id(),
            paid=paid_filter,
            origin_id=origin_filter if origin_filter else None,
            category_id=category_filter if category_filter else None,
            responsible_id=responsible_filter if responsible_filter else None,
            limit=500,
        )
    except Exception as e:
        st.error(f"Erro ao carregar dívidas: {e}")
        debts = []

    for d in debts:
        o_id = d.get_origin_id()
        if o_id is not None:
            origin_map.setdefault(str(o_id), f"Origem {o_id}")
        c_id = d.get_category_id()
        if c_id is not None:
            category_map.setdefault(str(c_id), f"Categoria {c_id}")
        r_id = d.get_responsible_id()
        if r_id is not None:
            responsible_map.setdefault(str(r_id), f"Responsável {r_id}")

    if not debts:
        st.info("Nenhum débito encontrado com os filtros selecionados.")
        return

    df = _df_from_debts(debts)
    df = df.set_index("id", drop=True)[
        [
            "sel",
            "origem",
            "categoria",
            "responsavel",
            "descricao",
            "data",
            "valor_total",
            "parcelas",
            "ultima_parcela",
            "pago",
            "notas",
        ]
    ]

    edited = st.data_editor(
        df,
        hide_index=True,
        width='stretch',
        column_config={
            "sel": st.column_config.CheckboxColumn("Selecionar", width="small"),
            "origem": st.column_config.SelectboxColumn(
                "Origem",
                options=list(origin_map.keys()),
                format_func=lambda key: origin_map.get(key, "Origem desconhecida"),
            ),
            "categoria": st.column_config.SelectboxColumn(
                "Categoria",
                options=list(category_map.keys()),
                format_func=lambda key: category_map.get(key, "Sem categoria"),
            ),
            "responsavel": st.column_config.SelectboxColumn(
                "Responsável",
                options=list(responsible_map.keys()),
                format_func=lambda key: responsible_map.get(key, "Sem responsável"),
            ),
            "descricao": st.column_config.TextColumn("Descrição", required=False),
            "data": st.column_config.DateColumn("Data"),
            "valor_total": st.column_config.NumberColumn("Valor total", min_value=0.01, format="%.2f"),
            "parcelas": st.column_config.NumberColumn("Parcelas", min_value=1, step=1),
            "ultima_parcela": st.column_config.DateColumn(
                "Última parcela",
                help="Calculada com base na data inicial e no número de parcelas",
                disabled=True,
            ),
            "pago": st.column_config.CheckboxColumn("Pago?"),
            "notas": st.column_config.TextColumn("Observações", required=False),
        },
        num_rows="fixed",
        key="debts_editor",
    )

    selected_ids = (
        edited.index[edited["sel"] == True].astype(int).tolist()
        if not edited.empty else []
    )

    if selected_ids:
        name_map = {d.get_id(): (d.get_description() or "(sem descrição)") for d in debts}
        preview = ", ".join(name_map.get(i, str(i)) for i in selected_ids)
        st.caption(f"Selecionados ({len(selected_ids)}): {preview}")

    spacer_left, center, spacer_right = st.columns([1, 4, 1])
    with center:
        btn_save, btn_delete = st.columns(2)
    with btn_save:
        if st.button("Salvar alterações", type="primary", key="save_debts", width='stretch'):
            altered = 0
            base = df.reset_index()[
                [
                    "id",
                    "origem",
                    "categoria",
                    "responsavel",
                    "descricao",
                    "data",
                    "valor_total",
                    "parcelas",
                    "pago",
                    "notas",
                ]
            ]
            curr = edited.reset_index()[
                [
                    "id",
                    "origem",
                    "categoria",
                    "responsavel",
                    "descricao",
                    "data",
                    "valor_total",
                    "parcelas",
                    "pago",
                    "notas",
                ]
            ]
            base = base.fillna({"descricao": "", "notas": "", "valor_total": 0.0, "parcelas": 1})
            curr = curr.fillna({"descricao": "", "notas": "", "valor_total": 0.0, "parcelas": 1})

            for _, row in curr.iterrows():
                orig = base.loc[base["id"] == row["id"]].iloc[0]
                changed = (
                    str(orig["origem"]) != str(row["origem"]) or
                    str(orig["categoria"]) != str(row["categoria"]) or
                    str(orig["responsavel"]) != str(row["responsavel"]) or
                    str(orig["descricao"]).strip() != str(row["descricao"]).strip() or
                    float(orig["valor_total"]) != float(row["valor_total"]) or
                    int(orig["parcelas"]) != int(row["parcelas"]) or
                    bool(orig["pago"]) != bool(row["pago"]) or
                    (orig["data"] != row["data"]) or
                    str(orig["notas"]).strip() != str(row["notas"]).strip()
                )
                if changed:
                    try:
                        debt = next(x for x in debts if x.get_id() == int(row["id"]))
                        debt.set_origin_id(int(row["origem"]))
                        debt.set_category_id(_str_to_opt(row["categoria"]))
                        debt.set_responsible_id(_str_to_opt(row["responsavel"]))
                        debt.set_description((str(row["descricao"]).strip() or None))
                        debt_date = row["data"]
                        if isinstance(debt_date, pd.Timestamp):
                            debt_date = debt_date.date()
                        debt.set_debt_date(debt_date)
                        debt.set_total_amount(float(row["valor_total"]))
                        debt.set_installments(int(row["parcelas"]))
                        debt.set_paid(bool(row["pago"]))
                        debt.set_notes((str(row["notas"]).strip() or None))
                        DebtRepository.update(debt)
                        altered += 1
                    except Exception as e:
                        st.error(f"Erro ao atualizar id={row['id']}: {e}")
            if altered:
                st.toast(f"{altered} alteração(ões) salva(s)", icon="✅")
                _do_rerun()
    with btn_delete:
        if st.button(
            f"Excluir selecionados ({len(selected_ids)})",
            disabled=len(selected_ids) == 0,
            key="delete_debts",
            width='stretch',
        ):
            st.session_state["confirm_delete_debts_ids"] = selected_ids
            _do_rerun()

    confirm_key = "confirm_delete_debts_ids"
    if st.session_state.get(confirm_key):
        ids = list(st.session_state.get(confirm_key, []))
        dialog = getattr(st, "dialog", None)
        if callable(dialog):
            @dialog("Confirmar exclusão")
            def _confirm_delete_dialog():
                st.write("Confirma a exclusão dos débitos selecionados?")
                if ids:
                    name_map = {d.get_id(): (d.get_description() or "(sem descrição)") for d in debts}
                    st.markdown("\n".join(f"- {name_map.get(i, str(i))}" for i in ids))
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("Cancelar", width='stretch'):
                        st.session_state[confirm_key] = []
                        _do_rerun()
                with col_b:
                    if st.button("Excluir", type="primary", width='stretch'):
                        removed = 0
                        for did in ids:
                            try:
                                DebtRepository.delete(int(did))
                                removed += 1
                            except Exception as e:
                                st.error(f"Erro ao remover id={did}: {e}")
                        st.session_state[confirm_key] = []
                        st.toast(f"{removed} débito(s) removido(s)", icon="✅")
                        _do_rerun()
            _confirm_delete_dialog()
        else:
            st.warning("Confirma a exclusão dos débitos selecionados?")
            if ids:
                name_map = {d.get_id(): (d.get_description() or "(sem descrição)") for d in debts}
                st.markdown("\n".join(f"- {name_map.get(i, str(i))}" for i in ids))
            col_a, col_b = st.columns(2)
            if col_a.button("Cancelar"):
                st.session_state[confirm_key] = []
                _do_rerun()
            if col_b.button("Excluir", type="primary"):
                removed = 0
                for did in ids:
                    try:
                        DebtRepository.delete(int(did))
                        removed += 1
                    except Exception as e:
                        st.error(f"Erro ao remover id={did}: {e}")
                st.session_state[confirm_key] = []
                st.toast(f"{removed} débito(s) removido(s)", icon="✅")
                _do_rerun()


render()
