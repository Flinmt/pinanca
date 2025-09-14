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
        "services.responsibles",
        "repository.users",
        "repository.responsibles",
    ]:
        if mod in sys.modules:
            del sys.modules[mod]

    import db.session as db_session
    import db.models as db_models
    db_session.init_db()

    import services.users as users
    import services.responsibles as responsibles
    import repository.users as users_repo
    import repository.responsibles as resp_repo
    return users, responsibles, users_repo, resp_repo


@pytest.fixture()
def mods(tmp_path):
    db_file = tmp_path / "test.db"
    return load_modules(str(db_file))


def test_create_and_get_by_id(mods):
    users, responsibles, users_repo, resp_repo = mods
    owner = users_repo.UserRepository.create(
        users.User(name="Owner", cpf="11122233344", password_hash=b"pw")
    )

    r = resp_repo.ResponsibleRepository.create(
        responsibles.Responsible(user_id=owner.get_id(), name="Kid", related_user_id=None)
    )
    assert r.get_id() is not None
    got = resp_repo.ResponsibleRepository.get_by_id(r.get_id())
    assert got is not None and got.get_name() == "Kid"


def test_list_by_user(mods):
    users, responsibles, users_repo, resp_repo = mods
    owner = users_repo.UserRepository.create(
        users.User(name="Owner2", cpf="00011122233", password_hash=b"pw")
    )
    created = [
        resp_repo.ResponsibleRepository.create(
            responsibles.Responsible(user_id=owner.get_id(), name=f"R{i}")
        )
        for i in range(3)
    ]

    lst = resp_repo.ResponsibleRepository.list_by_user(owner.get_id(), limit=2, offset=1)
    assert len(lst) == 2
    assert [x.get_id() for x in lst] == [created[1].get_id(), created[2].get_id()]


def test_update_responsible(mods):
    users, responsibles, users_repo, resp_repo = mods
    owner = users_repo.UserRepository.create(
        users.User(name="Owner3", cpf="99988877766", password_hash=b"pw")
    )
    r = resp_repo.ResponsibleRepository.create(
        responsibles.Responsible(user_id=owner.get_id(), name="Old")
    )

    r.set_name("New")
    updated = resp_repo.ResponsibleRepository.update(r)
    assert updated.get_name() == "New"


def test_update_without_id_raises(mods):
    users, responsibles, users_repo, resp_repo = mods
    owner = users_repo.UserRepository.create(
        users.User(name="Owner4", cpf="12312312312", password_hash=b"pw")
    )
    r = responsibles.Responsible(user_id=owner.get_id(), name="NoID")
    with pytest.raises(ValueError):
        resp_repo.ResponsibleRepository.update(r)


def test_update_nonexistent_responsible_raises(mods):
    users, responsibles, users_repo, resp_repo = mods
    owner = users_repo.UserRepository.create(
        users.User(name="Owner5", cpf="88877766655", password_hash=b"pw")
    )
    ghost = responsibles.Responsible(id=999999, user_id=owner.get_id(), name="Ghost")
    with pytest.raises(ValueError):
        resp_repo.ResponsibleRepository.update(ghost)


def test_create_with_invalid_user_raises(mods):
    _users, responsibles, _users_repo, resp_repo = mods
    with pytest.raises(ValueError):
        resp_repo.ResponsibleRepository.create(responsibles.Responsible(user_id=None, name="X"))


def test_create_with_empty_name_raises(mods):
    users, responsibles, users_repo, resp_repo = mods
    owner = users_repo.UserRepository.create(
        users.User(name="Owner6", cpf="32132132100", password_hash=b"pw")
    )
    with pytest.raises(ValueError):
        resp_repo.ResponsibleRepository.create(
            responsibles.Responsible(user_id=owner.get_id(), name="  ")
        )


def test_create_with_none_name_ok(mods):
    users, responsibles, users_repo, resp_repo = mods
    owner = users_repo.UserRepository.create(
        users.User(name="Owner7", cpf="10101010101", password_hash=b"pw")
    )
    r = resp_repo.ResponsibleRepository.create(
        responsibles.Responsible(user_id=owner.get_id(), name=None)
    )
    assert r.get_id() is not None


def test_delete_responsible(mods):
    users, responsibles, users_repo, resp_repo = mods
    owner = users_repo.UserRepository.create(
        users.User(name="Owner8", cpf="20202020202", password_hash=b"pw")
    )
    r1 = resp_repo.ResponsibleRepository.create(
        responsibles.Responsible(user_id=owner.get_id(), name="Del1")
    )
    r2 = resp_repo.ResponsibleRepository.create(
        responsibles.Responsible(user_id=owner.get_id(), name="Del2")
    )

    resp_repo.ResponsibleRepository.delete(r1.get_id())
    assert resp_repo.ResponsibleRepository.get_by_id(r1.get_id()) is None
    lst = resp_repo.ResponsibleRepository.list_by_user(owner.get_id())
    assert len(lst) == 1
    assert lst[0].get_id() == r2.get_id()

