import os
import sys
from pathlib import Path
import importlib

import pytest

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def load_modules(db_path: str):
    """Load db and services modules against an isolated SQLite DB file."""
    os.environ["DB_PATH"] = db_path

    # Clear SQLModel metadata and force clean imports
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
        "repository.users",
        "repository.categories",
    ]:
        if mod in sys.modules:
            del sys.modules[mod]

    import db.session as db_session
    import db.models as db_models
    db_session.init_db()

    import services.users as users
    import services.categories as categories
    import repository.users as users_repo
    import repository.categories as categories_repo
    return users, categories, users_repo, categories_repo


@pytest.fixture()
def mods(tmp_path):
    db_file = tmp_path / "test.db"
    return load_modules(str(db_file))


def test_create_and_get_by_id(mods):
    users, categories, users_repo, categories_repo = mods

    # create a user
    u = users_repo.UserRepository.create(
        users.User(name="Owner", cpf="11122233344", password_hash=b"pw")
    )

    cat = categories.Category(user_id=u.get_id(), name="Food")
    created = categories_repo.CategoryRepository.create(cat)

    assert created.get_id() is not None
    got = categories_repo.CategoryRepository.get_by_id(created.get_id())
    assert got is not None
    assert got.get_name() == "Food"
    assert got.get_user_id() == u.get_id()


def test_list_by_user_pagination(mods):
    users, categories, users_repo, categories_repo = mods
    u = users_repo.UserRepository.create(
        users.User(name="Owner2", cpf="00011122233", password_hash=b"pw")
    )

    created = [
        categories_repo.CategoryRepository.create(categories.Category(user_id=u.get_id(), name=f"C{i}"))
        for i in range(3)
    ]

    lst = categories_repo.CategoryRepository.list_by_user(u.get_id(), limit=2, offset=1)
    assert len(lst) == 2
    assert [c.get_id() for c in lst] == [created[1].get_id(), created[2].get_id()]


def test_update_category(mods):
    users, categories, users_repo, categories_repo = mods
    u = users_repo.UserRepository.create(
        users.User(name="Owner3", cpf="99988877766", password_hash=b"pw")
    )

    c = categories_repo.CategoryRepository.create(
        categories.Category(user_id=u.get_id(), name="Old")
    )

    c.set_name("New")
    updated = categories_repo.CategoryRepository.update(c)
    assert updated.get_name() == "New"


def test_update_without_id_raises(mods):
    users, categories, users_repo, categories_repo = mods
    u = users_repo.UserRepository.create(
        users.User(name="Owner4", cpf="12312312312", password_hash=b"pw")
    )
    c = categories.Category(user_id=u.get_id(), name="NoID")
    with pytest.raises(ValueError):
        categories_repo.CategoryRepository.update(c)


def test_update_nonexistent_category_raises(mods):
    users, categories, users_repo, categories_repo = mods
    u = users_repo.UserRepository.create(
        users.User(name="Owner5", cpf="88877766655", password_hash=b"pw")
    )
    ghost = categories.Category(id=999999, user_id=u.get_id(), name="Ghost")
    with pytest.raises(ValueError):
        categories_repo.CategoryRepository.update(ghost)


def test_create_with_invalid_user_raises(mods):
    _users, categories, _users_repo, categories_repo = mods
    with pytest.raises(ValueError):
        categories_repo.CategoryRepository.create(categories.Category(user_id=None, name="X"))


def test_create_with_empty_name_raises(mods):
    users, categories, users_repo, categories_repo = mods
    u = users_repo.UserRepository.create(
        users.User(name="Owner6", cpf="32132132100", password_hash=b"pw")
    )
    with pytest.raises(ValueError):
        categories_repo.CategoryRepository.create(categories.Category(user_id=u.get_id(), name="  "))


def test_delete_category(mods):
    users, categories, users_repo, categories_repo = mods
    u = users_repo.UserRepository.create(
        users.User(name="Owner7", cpf="10101010101", password_hash=b"pw")
    )

    c1 = categories_repo.CategoryRepository.create(categories.Category(user_id=u.get_id(), name="Del1"))
    c2 = categories_repo.CategoryRepository.create(categories.Category(user_id=u.get_id(), name="Del2"))

    # Apaga a primeira categoria
    categories_repo.CategoryRepository.delete(c1.get_id())

    assert categories_repo.CategoryRepository.get_by_id(c1.get_id()) is None
    lst = categories_repo.CategoryRepository.list_by_user(u.get_id())
    assert len(lst) == 1
    assert lst[0].get_id() == c2.get_id()
