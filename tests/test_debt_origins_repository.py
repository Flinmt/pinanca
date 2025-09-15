import os
import sys
from pathlib import Path
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
        "repository.users",
        "repository.debt_origins",
    ]:
        if mod in sys.modules:
            del sys.modules[mod]

    import db.session as db_session
    import db.models as db_models
    db_session.init_db()

    import services.users as users
    import services.debt_origins as debt_origins
    import repository.users as users_repo
    import repository.debt_origins as origins_repo
    return users, debt_origins, users_repo, origins_repo


@pytest.fixture()
def mods(tmp_path):
    db_file = tmp_path / "test.db"
    return load_modules(str(db_file))


def test_create_and_get_by_id(mods):
    users, debt_origins, users_repo, origins_repo = mods
    owner = users_repo.UserRepository.create(
        users.User(name="Owner", cpf="11122233344", password_hash=b"pw")
    )

    o = origins_repo.DebtOriginRepository.create(
        debt_origins.DebtOrigin(user_id=owner.get_id(), name="Bank")
    )
    assert o.get_id() is not None
    got = origins_repo.DebtOriginRepository.get_by_id(o.get_id())
    assert got is not None and got.get_name() == "Bank"


def test_list_by_user_pagination(mods):
    users, debt_origins, users_repo, origins_repo = mods
    owner = users_repo.UserRepository.create(
        users.User(name="Owner2", cpf="00011122233", password_hash=b"pw")
    )
    created = [
        origins_repo.DebtOriginRepository.create(
            debt_origins.DebtOrigin(user_id=owner.get_id(), name=f"O{i}")
        )
        for i in range(3)
    ]

    lst = origins_repo.DebtOriginRepository.list_by_user(owner.get_id(), limit=2, offset=1)
    assert len(lst) == 2
    assert [x.get_id() for x in lst] == [created[1].get_id(), created[2].get_id()]


def test_update_debt_origin(mods):
    users, debt_origins, users_repo, origins_repo = mods
    owner = users_repo.UserRepository.create(
        users.User(name="Owner3", cpf="99988877766", password_hash=b"pw")
    )
    o = origins_repo.DebtOriginRepository.create(
        debt_origins.DebtOrigin(user_id=owner.get_id(), name="Old")
    )

    o.set_name("New")
    updated = origins_repo.DebtOriginRepository.update(o)
    assert updated.get_name() == "New"


def test_update_without_id_raises(mods):
    users, debt_origins, users_repo, origins_repo = mods
    owner = users_repo.UserRepository.create(
        users.User(name="Owner4", cpf="12312312312", password_hash=b"pw")
    )
    o = debt_origins.DebtOrigin(user_id=owner.get_id(), name="NoID")
    with pytest.raises(ValueError):
        origins_repo.DebtOriginRepository.update(o)


def test_update_nonexistent_debt_origin_raises(mods):
    users, debt_origins, users_repo, origins_repo = mods
    owner = users_repo.UserRepository.create(
        users.User(name="Owner5", cpf="88877766655", password_hash=b"pw")
    )
    ghost = debt_origins.DebtOrigin(id=999999, user_id=owner.get_id(), name="Ghost")
    with pytest.raises(ValueError):
        origins_repo.DebtOriginRepository.update(ghost)


def test_create_with_invalid_user_raises(mods):
    _users, debt_origins, _users_repo, origins_repo = mods
    with pytest.raises(ValueError):
        origins_repo.DebtOriginRepository.create(debt_origins.DebtOrigin(user_id=None, name="X"))


def test_create_with_empty_name_raises(mods):
    users, debt_origins, users_repo, origins_repo = mods
    owner = users_repo.UserRepository.create(
        users.User(name="Owner6", cpf="32132132100", password_hash=b"pw")
    )
    with pytest.raises(ValueError):
        origins_repo.DebtOriginRepository.create(
            debt_origins.DebtOrigin(user_id=owner.get_id(), name="  ")
        )


def test_delete_debt_origin(mods):
    users, debt_origins, users_repo, origins_repo = mods
    owner = users_repo.UserRepository.create(
        users.User(name="Owner7", cpf="10101010101", password_hash=b"pw")
    )
    o1 = origins_repo.DebtOriginRepository.create(
        debt_origins.DebtOrigin(user_id=owner.get_id(), name="Del1")
    )
    o2 = origins_repo.DebtOriginRepository.create(
        debt_origins.DebtOrigin(user_id=owner.get_id(), name="Del2")
    )

    origins_repo.DebtOriginRepository.delete(o1.get_id())
    assert origins_repo.DebtOriginRepository.get_by_id(o1.get_id()) is None
    lst = origins_repo.DebtOriginRepository.list_by_user(owner.get_id())
    assert len(lst) == 1
    assert lst[0].get_id() == o2.get_id()

