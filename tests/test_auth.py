import os
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
import pytest

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def load_env_and_modules(db_path: str):
    os.environ["DB_PATH"] = db_path
    os.environ["AUTH_SECRET"] = "test-secret"

    from sqlmodel import SQLModel
    try:
        SQLModel.metadata.clear()
    except Exception:
        pass
    for mod in [
        "db.session",
        "db.models",
        "services.users",
        "repository.users",
        "core.config",
        "core.auth",
    ]:
        if mod in sys.modules:
            del sys.modules[mod]

    import db.session as db_session
    import db.models as db_models
    db_session.init_db()

    import services.users as users
    import repository.users as users_repo
    import core.auth as auth
    return users, users_repo, auth


@pytest.fixture()
def mods(tmp_path):
    db_file = tmp_path / "test.db"
    return load_env_and_modules(str(db_file))


def test_password_hash_and_verify(mods):
    _users, _users_repo, auth = mods
    h = auth.hash_password("secret")
    assert isinstance(h, (bytes, bytearray))
    assert auth.verify_password("secret", h) is True
    assert auth.verify_password("wrong", h) is False


def test_login_and_verify_session(mods):
    users, users_repo, auth = mods
    pwd_hash = auth.hash_password("pw123")
    u = users_repo.UserRepository.create(users.User(name="Alice", cpf="11122233344", password_hash=pwd_hash))

    token = auth.login("11122233344", "pw123")
    payload = auth.verify_session(token)
    assert payload["sub"] == u.get_id()

    with pytest.raises(auth.AuthError):
        auth.login("11122233344", "wrong")


def test_expired_session(mods):
    users, users_repo, auth = mods
    pwd_hash = auth.hash_password("pw")
    u = users_repo.UserRepository.create(users.User(name="Bob", cpf="00011122233", password_hash=pwd_hash))

    past = datetime.now(timezone.utc) - timedelta(seconds=10)
    token = auth.issue_session(u.get_id(), expires_in=1, now=past)
    with pytest.raises(auth.AuthError):
        auth.verify_session(token)

