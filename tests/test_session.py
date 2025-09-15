import os
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
import json
import pytest

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def setup_env(tmpdir: Path):
    os.environ["DB_PATH"] = str(tmpdir / "test.db")
    os.environ["AUTH_SECRET"] = "test-secret"
    os.environ["SESSION_FILE"] = str(tmpdir / "session.json")


def load_modules():
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
        "core.session",
    ]:
        if mod in sys.modules:
            del sys.modules[mod]

    import db.session as db_session
    import db.models as db_models
    db_session.init_db()

    import services.users as users
    import repository.users as users_repo
    import core.auth as auth
    import core.session as session
    return users, users_repo, auth, session


@pytest.fixture()
def mods(tmp_path):
    setup_env(tmp_path)
    return load_modules()


def test_login_persist_and_current_user(mods):
    users, users_repo, auth, session = mods
    # create user with hashed password
    pwd_hash = auth.hash_password("pw123")
    u = users_repo.UserRepository.create(users.User(name="SessUser", cpf="11122233344", password_hash=pwd_hash))

    uid = session.login_and_persist("11122233344", "pw123")
    assert uid == u.get_id()

    current = session.current_user()
    assert current is not None
    assert current.get_id() == u.get_id()

    # file exists with token
    sess_path = Path(os.environ["SESSION_FILE"])    
    assert sess_path.exists()
    data = json.loads(sess_path.read_text())
    assert isinstance(data.get("token"), str)

    # logout clears file and current_user
    session.logout()
    assert not sess_path.exists()
    assert session.current_user() is None


def test_current_user_clears_expired(mods, tmp_path):
    users, users_repo, auth, session = mods
    # create user
    pwd_hash = auth.hash_password("pw")
    u = users_repo.UserRepository.create(users.User(name="Expire", cpf="00011122233", password_hash=pwd_hash))

    # issue expired token and save
    past = datetime.now(timezone.utc) - timedelta(seconds=10)
    token = auth.issue_session(u.get_id(), expires_in=1, now=past)
    session.save_token(token)

    # current_user should clear invalid token and return None
    assert session.current_user() is None
    assert not Path(os.environ["SESSION_FILE"]).exists()
