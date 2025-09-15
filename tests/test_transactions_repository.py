import os
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
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
        "services.categories",
        "services.transactions",
        "repository.users",
        "repository.categories",
        "repository.transactions",
    ]:
        if mod in sys.modules:
            del sys.modules[mod]

    import db.session as db_session
    import db.models as db_models
    db_session.init_db()

    import services.users as users
    import services.categories as categories
    import services.transactions as transactions
    import repository.users as users_repo
    import repository.categories as categories_repo
    import repository.transactions as tx_repo
    return users, categories, transactions, users_repo, categories_repo, tx_repo


@pytest.fixture()
def mods(tmp_path):
    db_file = tmp_path / "test.db"
    return load_modules(str(db_file))


def test_create_and_get_by_id(mods):
    users, categories, transactions, users_repo, categories_repo, tx_repo = mods
    u = users_repo.UserRepository.create(users.User(name="Owner", cpf="11122233344", password_hash=b"pw"))
    c = categories_repo.CategoryRepository.create(categories.Category(user_id=u.get_id(), name="Cat"))

    t = tx_repo.TransactionRepository.create(
        transactions.Transaction(user_id=u.get_id(), category_id=c.get_id(), amount=100.0, type="income", description="Salário")
    )
    assert t.get_id() is not None
    got = tx_repo.TransactionRepository.get_by_id(t.get_id())
    assert got is not None and got.get_amount() == 100.0 and got.get_type() == "income"


def test_list_by_user_and_filters(mods):
    users, categories, transactions, users_repo, categories_repo, tx_repo = mods
    u = users_repo.UserRepository.create(users.User(name="Owner2", cpf="00011122233", password_hash=b"pw"))
    c1 = categories_repo.CategoryRepository.create(categories.Category(user_id=u.get_id(), name="Food"))
    c2 = categories_repo.CategoryRepository.create(categories.Category(user_id=u.get_id(), name="Salary"))

    now = datetime.now(timezone.utc)
    earlier = now - timedelta(days=10)
    later = now + timedelta(days=10)

    t1 = tx_repo.TransactionRepository.create(transactions.Transaction(user_id=u.get_id(), category_id=c1.get_id(), amount=30.0, type="expense", occurred_at=earlier, description="Groceries"))
    t2 = tx_repo.TransactionRepository.create(transactions.Transaction(user_id=u.get_id(), category_id=c2.get_id(), amount=2000.0, type="income", occurred_at=now, description="Salary"))
    t3 = tx_repo.TransactionRepository.create(transactions.Transaction(user_id=u.get_id(), category_id=c1.get_id(), amount=50.0, type="expense", occurred_at=later, description="Dining"))

    # list_by_user ordered desc by occurred_at
    lst = tx_repo.TransactionRepository.list_by_user(u.get_id())
    assert [x.get_id() for x in lst] == [t3.get_id(), t2.get_id(), t1.get_id()]

    # filter by type
    expenses = tx_repo.TransactionRepository.list_by_filters(u.get_id(), type="expense")
    assert [x.get_id() for x in expenses] == [t3.get_id(), t1.get_id()]

    # filter by category
    only_c2 = tx_repo.TransactionRepository.list_by_filters(u.get_id(), category_id=c2.get_id())
    assert [x.get_id() for x in only_c2] == [t2.get_id()]

    # amount range
    mid = tx_repo.TransactionRepository.list_by_filters(u.get_id(), min_amount=40, max_amount=100)
    assert [x.get_id() for x in mid] == [t3.get_id()]

    # date range
    between = tx_repo.TransactionRepository.list_by_filters(u.get_id(), start=earlier + timedelta(days=1), end=later - timedelta(days=1))
    assert [x.get_id() for x in between] == [t2.get_id()]


def test_update_and_delete(mods):
    users, categories, transactions, users_repo, categories_repo, tx_repo = mods
    u = users_repo.UserRepository.create(users.User(name="Owner3", cpf="99988877766", password_hash=b"pw"))
    c = categories_repo.CategoryRepository.create(categories.Category(user_id=u.get_id(), name="Misc"))

    t = tx_repo.TransactionRepository.create(transactions.Transaction(user_id=u.get_id(), category_id=c.get_id(), amount=10.0, type="expense", description="x"))
    t.set_amount(12.5)
    t.set_type("expense")
    t.set_description("updated")
    updated = tx_repo.TransactionRepository.update(t)
    assert updated.get_amount() == 12.5
    assert updated.get_description() == "updated"

    tx_repo.TransactionRepository.delete(updated.get_id())
    assert tx_repo.TransactionRepository.get_by_id(updated.get_id()) is None


def test_validations(mods):
    users, categories, transactions, users_repo, categories_repo, tx_repo = mods
    u = users_repo.UserRepository.create(users.User(name="Owner4", cpf="12312312312", password_hash=b"pw"))
    with pytest.raises(ValueError):
        tx_repo.TransactionRepository.create(transactions.Transaction(user_id=u.get_id(), amount=0, type="income"))
    with pytest.raises(ValueError):
        tx_repo.TransactionRepository.create(transactions.Transaction(user_id=u.get_id(), amount=10, type="unknown"))
    with pytest.raises(ValueError):
        tx_repo.TransactionRepository.create(transactions.Transaction(user_id=None, amount=10, type="income"))

