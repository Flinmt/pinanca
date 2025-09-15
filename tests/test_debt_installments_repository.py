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
        "services.debt_installments",
        "repository.users",
        "repository.debt_origins",
        "repository.debt_installments",
    ]:
        if mod in sys.modules:
            del sys.modules[mod]

    import db.session as db_session
    import db.models as db_models
    db_session.init_db()

    import services.users as users
    import services.debt_origins as origins
    import services.debt_installments as inst
    import repository.users as users_repo
    import repository.debt_origins as origins_repo
    import repository.debt_installments as inst_repo
    return users, origins, inst, users_repo, origins_repo, inst_repo, db_models


def create_debt(db_models, user_id: int, origin_id: int):
    from sqlmodel import Session
    from db.session import engine

    with Session(engine) as s:
        debt = db_models.Debt(
            user_id=user_id,
            origin_id=origin_id,
            category_id=None,
            responsible_id=None,
            debt_date=date.today(),
            description=None,
            total_amount=300.0,
            installments=3,
            notes=None,
            paid=False,
        )
        s.add(debt)
        s.commit()
        s.refresh(debt)
        return debt.id


@pytest.fixture()
def mods(tmp_path):
    db_file = tmp_path / "test.db"
    return load_modules(str(db_file))


def test_create_and_get_by_id(mods):
    users, origins, inst, users_repo, origins_repo, inst_repo, db_models = mods
    owner = users_repo.UserRepository.create(
        users.User(name="Owner", cpf="11122233344", password_hash=b"pw")
    )
    origin = origins_repo.DebtOriginRepository.create(
        origins.DebtOrigin(user_id=owner.get_id(), name="Bank")
    )
    debt_id = create_debt(db_models, owner.get_id(), origin.get_id())

    i = inst_repo.DebtInstallmentRepository.create(
        inst.DebtInstallment(debt_id=debt_id, number=1, amount=100.0, due_on=date(2025, 1, 31))
    )
    assert i.get_id() is not None
    got = inst_repo.DebtInstallmentRepository.get_by_id(i.get_id())
    assert got is not None and got.get_number() == 1 and got.get_amount() == 100.0


def test_list_by_debt_pagination(mods):
    users, origins, inst, users_repo, origins_repo, inst_repo, db_models = mods
    owner = users_repo.UserRepository.create(
        users.User(name="Owner2", cpf="00011122233", password_hash=b"pw")
    )
    origin = origins_repo.DebtOriginRepository.create(
        origins.DebtOrigin(user_id=owner.get_id(), name="Store")
    )
    debt_id = create_debt(db_models, owner.get_id(), origin.get_id())

    created = [
        inst_repo.DebtInstallmentRepository.create(
            inst.DebtInstallment(debt_id=debt_id, number=i + 1, amount=50.0, due_on=date(2025, 2, i + 1))
        )
        for i in range(3)
    ]

    lst = inst_repo.DebtInstallmentRepository.list_by_debt(debt_id, limit=2, offset=1)
    assert len(lst) == 2
    assert [x.get_id() for x in lst] == [created[1].get_id(), created[2].get_id()]


def test_update_installment_paid_flags(mods):
    users, origins, inst, users_repo, origins_repo, inst_repo, db_models = mods
    owner = users_repo.UserRepository.create(
        users.User(name="Owner3", cpf="99988877766", password_hash=b"pw")
    )
    origin = origins_repo.DebtOriginRepository.create(
        origins.DebtOrigin(user_id=owner.get_id(), name="Loan")
    )
    debt_id = create_debt(db_models, owner.get_id(), origin.get_id())

    i = inst_repo.DebtInstallmentRepository.create(
        inst.DebtInstallment(debt_id=debt_id, number=1, amount=120.0, due_on=date(2025, 3, 15))
    )
    assert i.get_paid() is False and i.get_paid_at() is None

    i.set_paid(True)
    updated = inst_repo.DebtInstallmentRepository.update(i)
    assert updated.get_paid() is True
    assert updated.get_paid_at() is not None

    # Now unset paid and ensure paid_at clears
    updated.set_paid(False)
    updated2 = inst_repo.DebtInstallmentRepository.update(updated)
    assert updated2.get_paid() is False
    assert updated2.get_paid_at() is None


def test_update_without_id_raises(mods):
    users, origins, inst, users_repo, origins_repo, inst_repo, db_models = mods
    owner = users_repo.UserRepository.create(
        users.User(name="Owner4", cpf="12312312312", password_hash=b"pw")
    )
    origin = origins_repo.DebtOriginRepository.create(
        origins.DebtOrigin(user_id=owner.get_id(), name="Shop")
    )
    debt_id = create_debt(db_models, owner.get_id(), origin.get_id())
    i = inst.DebtInstallment(debt_id=debt_id, number=1, amount=10.0, due_on=date(2025, 4, 10))
    with pytest.raises(ValueError):
        inst_repo.DebtInstallmentRepository.update(i)


def test_update_nonexistent_installment_raises(mods):
    users, origins, inst, users_repo, origins_repo, inst_repo, db_models = mods
    owner = users_repo.UserRepository.create(
        users.User(name="Owner5", cpf="88877766655", password_hash=b"pw")
    )
    origin = origins_repo.DebtOriginRepository.create(
        origins.DebtOrigin(user_id=owner.get_id(), name="Other")
    )
    debt_id = create_debt(db_models, owner.get_id(), origin.get_id())
    ghost = inst.DebtInstallment(id=999999, debt_id=debt_id, number=1, amount=10.0, due_on=date(2025, 5, 10))
    with pytest.raises(ValueError):
        inst_repo.DebtInstallmentRepository.update(ghost)


def test_create_validations(mods):
    users, origins, inst, users_repo, origins_repo, inst_repo, db_models = mods
    owner = users_repo.UserRepository.create(
        users.User(name="Owner6", cpf="32132132100", password_hash=b"pw")
    )
    origin = origins_repo.DebtOriginRepository.create(
        origins.DebtOrigin(user_id=owner.get_id(), name="Origin")
    )
    debt_id = create_debt(db_models, owner.get_id(), origin.get_id())

    with pytest.raises(ValueError):
        inst_repo.DebtInstallmentRepository.create(
            inst.DebtInstallment(debt_id=debt_id, number=0, amount=10.0, due_on=date(2025, 6, 10))
        )
    with pytest.raises(ValueError):
        inst_repo.DebtInstallmentRepository.create(
            inst.DebtInstallment(debt_id=debt_id, number=1, amount=0.0, due_on=date(2025, 6, 10))
        )
    with pytest.raises(ValueError):
        inst_repo.DebtInstallmentRepository.create(
            inst.DebtInstallment(debt_id=debt_id, number=1, amount=10.0, due_on=None)
        )


def test_delete_installment(mods):
    users, origins, inst, users_repo, origins_repo, inst_repo, db_models = mods
    owner = users_repo.UserRepository.create(
        users.User(name="Owner7", cpf="10101010101", password_hash=b"pw")
    )
    origin = origins_repo.DebtOriginRepository.create(
        origins.DebtOrigin(user_id=owner.get_id(), name="X")
    )
    debt_id = create_debt(db_models, owner.get_id(), origin.get_id())

    i1 = inst_repo.DebtInstallmentRepository.create(
        inst.DebtInstallment(debt_id=debt_id, number=1, amount=10.0, due_on=date(2025, 7, 1))
    )
    i2 = inst_repo.DebtInstallmentRepository.create(
        inst.DebtInstallment(debt_id=debt_id, number=2, amount=20.0, due_on=date(2025, 8, 1))
    )

    inst_repo.DebtInstallmentRepository.delete(i1.get_id())
    assert inst_repo.DebtInstallmentRepository.get_by_id(i1.get_id()) is None
    lst = inst_repo.DebtInstallmentRepository.list_by_debt(debt_id)
    assert len(lst) == 1
    assert lst[0].get_id() == i2.get_id()

