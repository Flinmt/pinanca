import os
import sys
from pathlib import Path
from datetime import date
import pytest

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def load_modules(db_path: str):
    os.environ["DB_PATH"] = db_path
    from sqlmodel import SQLModel
    try:
        SQLModel.metadata.clear()
    except Exception:
        pass
    for mod in [
        "db.session",
        "db.models",
        "services.users",
        "services.debt_origins",
        "services.categories",
        "services.responsibles",
        "services.debts",
        "repository.users",
        "repository.debt_origins",
        "repository.categories",
        "repository.responsibles",
        "repository.debts",
    ]:
        if mod in sys.modules:
            del sys.modules[mod]

    import db.session as db_session
    import db.models as db_models
    db_session.init_db()

    import services.users as users
    import services.debt_origins as origins
    import services.categories as categories
    import services.responsibles as responsibles
    import services.debts as debts
    import repository.users as users_repo
    import repository.debt_origins as origins_repo
    import repository.categories as categories_repo
    import repository.responsibles as responsibles_repo
    import repository.debts as debts_repo
    return users, origins, categories, responsibles, debts, users_repo, origins_repo, categories_repo, responsibles_repo, debts_repo


@pytest.fixture()
def mods(tmp_path):
    db_file = tmp_path / "test.db"
    return load_modules(str(db_file))


def test_create_and_get_by_id(mods):
    users, origins, categories, responsibles, debts, users_repo, origins_repo, categories_repo, responsibles_repo, debts_repo = mods
    u = users_repo.UserRepository.create(users.User(name="Owner", cpf="11122233344", password_hash=b"pw"))
    o = origins_repo.DebtOriginRepository.create(origins.DebtOrigin(user_id=u.get_id(), name="Bank"))

    d = debts_repo.DebtRepository.create(
        debts.Debt(user_id=u.get_id(), origin_id=o.get_id(), category_id=None, responsible_id=None, debt_date=date(2025, 1, 1), total_amount=100.0, installments=2)
    )
    assert d.get_id() is not None
    got = debts_repo.DebtRepository.get_by_id(d.get_id())
    assert got is not None and got.get_total_amount() == 100.0 and got.get_installments() == 2


def test_list_by_user_pagination(mods):
    users, origins, categories, responsibles, debts, users_repo, origins_repo, categories_repo, responsibles_repo, debts_repo = mods
    u = users_repo.UserRepository.create(users.User(name="Owner2", cpf="00011122233", password_hash=b"pw"))
    o = origins_repo.DebtOriginRepository.create(origins.DebtOrigin(user_id=u.get_id(), name="Store"))

    created = [
        debts_repo.DebtRepository.create(
            debts.Debt(user_id=u.get_id(), origin_id=o.get_id(), debt_date=date(2025, 2, i + 1), total_amount=50.0, installments=1)
        )
        for i in range(3)
    ]

    lst = debts_repo.DebtRepository.list_by_user(u.get_id(), limit=2, offset=1)
    assert len(lst) == 2
    assert [x.get_id() for x in lst] == [created[1].get_id(), created[2].get_id()]


def test_update_debt(mods):
    users, origins, categories, responsibles, debts, users_repo, origins_repo, categories_repo, responsibles_repo, debts_repo = mods
    u = users_repo.UserRepository.create(users.User(name="Owner3", cpf="99988877766", password_hash=b"pw"))
    o = origins_repo.DebtOriginRepository.create(origins.DebtOrigin(user_id=u.get_id(), name="Loan"))

    d = debts_repo.DebtRepository.create(
        debts.Debt(user_id=u.get_id(), origin_id=o.get_id(), debt_date=date(2025, 3, 10), total_amount=200.0, installments=4, description=None, notes=None)
    )

    d.set_paid(True)
    d.set_total_amount(250.0)
    d.set_description("Updated")
    updated = debts_repo.DebtRepository.update(d)
    assert updated.get_paid() is True
    assert updated.get_total_amount() == 250.0
    assert updated.get_description() == "Updated"


def test_update_without_id_raises(mods):
    users, origins, categories, responsibles, debts, users_repo, origins_repo, categories_repo, responsibles_repo, debts_repo = mods
    u = users_repo.UserRepository.create(users.User(name="Owner4", cpf="12312312312", password_hash=b"pw"))
    o = origins_repo.DebtOriginRepository.create(origins.DebtOrigin(user_id=u.get_id(), name="Shop"))
    ghost = debts.Debt(user_id=u.get_id(), origin_id=o.get_id(), debt_date=date(2025, 4, 1), total_amount=10.0, installments=1)
    with pytest.raises(ValueError):
        debts_repo.DebtRepository.update(ghost)


def test_update_nonexistent_debt_raises(mods):
    users, origins, categories, responsibles, debts, users_repo, origins_repo, categories_repo, responsibles_repo, debts_repo = mods
    u = users_repo.UserRepository.create(users.User(name="Owner5", cpf="88877766655", password_hash=b"pw"))
    o = origins_repo.DebtOriginRepository.create(origins.DebtOrigin(user_id=u.get_id(), name="Other"))
    ghost = debts.Debt(id=999999, user_id=u.get_id(), origin_id=o.get_id(), debt_date=date(2025, 5, 1), total_amount=10.0, installments=1)
    with pytest.raises(ValueError):
        debts_repo.DebtRepository.update(ghost)


def test_create_validations(mods):
    users, origins, categories, responsibles, debts, users_repo, origins_repo, categories_repo, responsibles_repo, debts_repo = mods
    u = users_repo.UserRepository.create(users.User(name="Owner6", cpf="32132132100", password_hash=b"pw"))
    with pytest.raises(ValueError):
        debts_repo.DebtRepository.create(debts.Debt(user_id=u.get_id(), origin_id=None, debt_date=date(2025, 6, 1), total_amount=10.0, installments=1))
    with pytest.raises(ValueError):
        debts_repo.DebtRepository.create(debts.Debt(user_id=None, origin_id=1, debt_date=date(2025, 6, 1), total_amount=10.0, installments=1))
    with pytest.raises(ValueError):
        debts_repo.DebtRepository.create(debts.Debt(user_id=u.get_id(), origin_id=1, debt_date=None, total_amount=10.0, installments=1))
    with pytest.raises(ValueError):
        debts_repo.DebtRepository.create(debts.Debt(user_id=u.get_id(), origin_id=1, debt_date=date(2025, 6, 1), total_amount=0.0, installments=1))
    with pytest.raises(ValueError):
        debts_repo.DebtRepository.create(debts.Debt(user_id=u.get_id(), origin_id=1, debt_date=date(2025, 6, 1), total_amount=10.0, installments=0))


def test_delete_debt(mods):
    users, origins, categories, responsibles, debts, users_repo, origins_repo, categories_repo, responsibles_repo, debts_repo = mods
    u = users_repo.UserRepository.create(users.User(name="Owner7", cpf="10101010101", password_hash=b"pw"))
    o = origins_repo.DebtOriginRepository.create(origins.DebtOrigin(user_id=u.get_id(), name="X"))
    d1 = debts_repo.DebtRepository.create(debts.Debt(user_id=u.get_id(), origin_id=o.get_id(), debt_date=date(2025, 7, 1), total_amount=10.0, installments=1))
    d2 = debts_repo.DebtRepository.create(debts.Debt(user_id=u.get_id(), origin_id=o.get_id(), debt_date=date(2025, 7, 2), total_amount=20.0, installments=2))

    debts_repo.DebtRepository.delete(d1.get_id())
    assert debts_repo.DebtRepository.get_by_id(d1.get_id()) is None
    lst = debts_repo.DebtRepository.list_by_user(u.get_id())
    assert len(lst) == 1
    assert lst[0].get_id() == d2.get_id()


def test_filter_by_paid(mods):
    users, origins, categories, responsibles, debts, users_repo, origins_repo, categories_repo, responsibles_repo, debts_repo = mods
    u = users_repo.UserRepository.create(users.User(name="Owner8", cpf="20202020202", password_hash=b"pw"))
    o = origins_repo.DebtOriginRepository.create(origins.DebtOrigin(user_id=u.get_id(), name="Y"))
    d1 = debts_repo.DebtRepository.create(debts.Debt(user_id=u.get_id(), origin_id=o.get_id(), debt_date=date(2025, 8, 1), total_amount=10.0, installments=1, paid=False))
    d2 = debts_repo.DebtRepository.create(debts.Debt(user_id=u.get_id(), origin_id=o.get_id(), debt_date=date(2025, 8, 2), total_amount=20.0, installments=2, paid=True))
    d3 = debts_repo.DebtRepository.create(debts.Debt(user_id=u.get_id(), origin_id=o.get_id(), debt_date=date(2025, 8, 3), total_amount=30.0, installments=3, paid=False))

    open_debts = debts_repo.DebtRepository.list_by_user_and_paid(u.get_id(), paid=False)
    paid_debts = debts_repo.DebtRepository.list_by_user_and_paid(u.get_id(), paid=True)

    assert [x.get_id() for x in open_debts] == [d1.get_id(), d3.get_id()]
    assert [x.get_id() for x in paid_debts] == [d2.get_id()]


def test_filter_by_origin(mods):
    users, origins, categories, responsibles, debts, users_repo, origins_repo, categories_repo, responsibles_repo, debts_repo = mods
    u = users_repo.UserRepository.create(users.User(name="Owner9", cpf="30303030303", password_hash=b"pw"))
    o1 = origins_repo.DebtOriginRepository.create(origins.DebtOrigin(user_id=u.get_id(), name="O1"))
    o2 = origins_repo.DebtOriginRepository.create(origins.DebtOrigin(user_id=u.get_id(), name="O2"))
    d1 = debts_repo.DebtRepository.create(debts.Debt(user_id=u.get_id(), origin_id=o1.get_id(), debt_date=date(2025, 9, 1), total_amount=10.0, installments=1))
    d2 = debts_repo.DebtRepository.create(debts.Debt(user_id=u.get_id(), origin_id=o2.get_id(), debt_date=date(2025, 9, 2), total_amount=20.0, installments=2))
    d3 = debts_repo.DebtRepository.create(debts.Debt(user_id=u.get_id(), origin_id=o1.get_id(), debt_date=date(2025, 9, 3), total_amount=30.0, installments=3))

    only_o1 = debts_repo.DebtRepository.list_by_user_and_origin(u.get_id(), o1.get_id())
    assert [x.get_id() for x in only_o1] == [d1.get_id(), d3.get_id()]


def test_filter_by_date_range(mods):
    users, origins, categories, responsibles, debts, users_repo, origins_repo, categories_repo, responsibles_repo, debts_repo = mods
    u = users_repo.UserRepository.create(users.User(name="Owner10", cpf="40404040404", password_hash=b"pw"))
    o = origins_repo.DebtOriginRepository.create(origins.DebtOrigin(user_id=u.get_id(), name="O"))
    d1 = debts_repo.DebtRepository.create(debts.Debt(user_id=u.get_id(), origin_id=o.get_id(), debt_date=date(2025, 10, 1), total_amount=10.0, installments=1))
    d2 = debts_repo.DebtRepository.create(debts.Debt(user_id=u.get_id(), origin_id=o.get_id(), debt_date=date(2025, 10, 15), total_amount=20.0, installments=2))
    d3 = debts_repo.DebtRepository.create(debts.Debt(user_id=u.get_id(), origin_id=o.get_id(), debt_date=date(2025, 11, 1), total_amount=30.0, installments=3))

    mid_month = debts_repo.DebtRepository.list_by_user_and_date_range(u.get_id(), start_date=date(2025, 10, 2), end_date=date(2025, 10, 31))
    from_mid = debts_repo.DebtRepository.list_by_user_and_date_range(u.get_id(), start_date=date(2025, 10, 15))
    until_mid = debts_repo.DebtRepository.list_by_user_and_date_range(u.get_id(), end_date=date(2025, 10, 15))

    assert [x.get_id() for x in mid_month] == [d2.get_id()]
    assert [x.get_id() for x in from_mid] == [d2.get_id(), d3.get_id()]
    assert [x.get_id() for x in until_mid] == [d1.get_id(), d2.get_id()]


def test_combined_filters(mods):
    users, origins, categories, responsibles, debts, users_repo, origins_repo, categories_repo, responsibles_repo, debts_repo = mods
    u = users_repo.UserRepository.create(users.User(name="Owner11", cpf="50505050505", password_hash=b"pw"))
    o1 = origins_repo.DebtOriginRepository.create(origins.DebtOrigin(user_id=u.get_id(), name="O1"))
    o2 = origins_repo.DebtOriginRepository.create(origins.DebtOrigin(user_id=u.get_id(), name="O2"))
    c1 = categories_repo.CategoryRepository.create(categories.Category(user_id=u.get_id(), name="C1"))
    c2 = categories_repo.CategoryRepository.create(categories.Category(user_id=u.get_id(), name="C2"))
    r1 = responsibles_repo.ResponsibleRepository.create(responsibles.Responsible(user_id=u.get_id(), name="R1"))

    d1 = debts_repo.DebtRepository.create(debts.Debt(user_id=u.get_id(), origin_id=o1.get_id(), category_id=c1.get_id(), responsible_id=None, debt_date=date(2025, 12, 1), total_amount=10.0, installments=1, paid=False))
    d2 = debts_repo.DebtRepository.create(debts.Debt(user_id=u.get_id(), origin_id=o1.get_id(), category_id=c1.get_id(), responsible_id=None, debt_date=date(2025, 12, 10), total_amount=20.0, installments=2, paid=True))
    d3 = debts_repo.DebtRepository.create(debts.Debt(user_id=u.get_id(), origin_id=o2.get_id(), category_id=c2.get_id(), responsible_id=None, debt_date=date(2026, 1, 5), total_amount=30.0, installments=3, paid=False))
    d4 = debts_repo.DebtRepository.create(debts.Debt(user_id=u.get_id(), origin_id=o1.get_id(), category_id=c2.get_id(), responsible_id=r1.get_id(), debt_date=date(2025, 12, 20), total_amount=40.0, installments=4, paid=False))

    # origin + category + paid
    res = debts_repo.DebtRepository.list_by_filters(u.get_id(), origin_id=o1.get_id(), category_id=c1.get_id(), paid=False)
    assert [x.get_id() for x in res] == [d1.get_id()]

    # origin + date range
    res2 = debts_repo.DebtRepository.list_by_filters(u.get_id(), origin_id=o1.get_id(), start_date=date(2025, 12, 2), end_date=date(2025, 12, 31))
    assert [x.get_id() for x in res2] == [d2.get_id(), d4.get_id()]

    # responsible only
    res3 = debts_repo.DebtRepository.list_by_filters(u.get_id(), responsible_id=r1.get_id())
    assert [x.get_id() for x in res3] == [d4.get_id()]


def test_filter_by_installments_range(mods):
    users, origins, categories, responsibles, debts, users_repo, origins_repo, categories_repo, responsibles_repo, debts_repo = mods
    u = users_repo.UserRepository.create(users.User(name="Owner12", cpf="60606060606", password_hash=b"pw"))
    o = origins_repo.DebtOriginRepository.create(origins.DebtOrigin(user_id=u.get_id(), name="Z"))

    d1 = debts_repo.DebtRepository.create(debts.Debt(user_id=u.get_id(), origin_id=o.get_id(), debt_date=date(2025, 1, 1), total_amount=10.0, installments=1))
    d2 = debts_repo.DebtRepository.create(debts.Debt(user_id=u.get_id(), origin_id=o.get_id(), debt_date=date(2025, 1, 2), total_amount=20.0, installments=2))
    d3 = debts_repo.DebtRepository.create(debts.Debt(user_id=u.get_id(), origin_id=o.get_id(), debt_date=date(2025, 1, 3), total_amount=30.0, installments=4))

    # Igual a 2 (min=max=2)
    eq2 = debts_repo.DebtRepository.list_by_filters(u.get_id(), installments_min=2, installments_max=2)
    assert [x.get_id() for x in eq2] == [d2.get_id()]

    # Faixa [2, 4]
    rng = debts_repo.DebtRepository.list_by_filters(u.get_id(), installments_min=2, installments_max=4)
    assert [x.get_id() for x in rng] == [d2.get_id(), d3.get_id()]

    # Somente mínimo (>=2)
    min_only = debts_repo.DebtRepository.list_by_filters(u.get_id(), installments_min=2)
    assert [x.get_id() for x in min_only] == [d2.get_id(), d3.get_id()]

    # Somente máximo (<=2)
    max_only = debts_repo.DebtRepository.list_by_filters(u.get_id(), installments_max=2)
    assert [x.get_id() for x in max_only] == [d1.get_id(), d2.get_id()]
