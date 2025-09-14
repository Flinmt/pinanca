import os
import sys
from pathlib import Path
import importlib
from datetime import datetime

import pytest

# Ensure project root is on sys.path for `import db` and `services`
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def load_users_module(db_path: str):
    """
    Configura o caminho do banco (arquivo SQLite), reinicializa os módulos
    que dependem do engine e retorna o módulo de serviços de usuários.
    """
    # Define o DB_PATH antes de importar os módulos que criam o engine
    os.environ["DB_PATH"] = db_path

    # Limpa metadata global do SQLModel para evitar duplicação de tabelas ao recarregar
    from sqlmodel import SQLModel
    try:
        SQLModel.metadata.clear()
    except Exception:
        pass

    # Remove módulos anteriores para forçar import limpo
    for mod in ["db.session", "db.models", "services.users", "repository.users"]:
        if mod in sys.modules:
            del sys.modules[mod]

    # Importa novamente sessão e modelos com o novo DB_PATH
    import db.session as db_session
    import db.models as db_models

    # Cria as tabelas no novo banco
    db_session.init_db()

    # Importa o serviço e o repositório para garantir referências atualizadas
    import services.users as users
    import repository.users as users_repo
    return users, users_repo


@pytest.fixture()
def user_mods(tmp_path):
    """Fornece módulos `services.users` e `repository.users` com DB isolado por teste."""
    db_file = tmp_path / "test.db"
    return load_users_module(str(db_file))


def test_create_and_get_by_id(user_mods):
    users, repos = user_mods
    Usuario = users.User
    Repo = repos.UserRepository

    novo = Usuario(name="Alice", cpf="11122233344", password_hash=b"hash", profile_image=None)
    criado = Repo.create(novo)

    assert criado.get_id() is not None
    assert criado.get_name() == "Alice"
    assert criado.get_cpf() == "11122233344"
    assert isinstance(criado.get_created_at(), datetime)

    recuperado = Repo.get_by_id(criado.get_id())
    assert recuperado is not None
    assert recuperado.get_cpf() == "11122233344"


def test_get_by_cpf(user_mods):
    users, repos = user_mods
    Usuario = users.User
    Repo = repos.UserRepository

    u1 = Repo.create(Usuario(name="Bob", cpf="00011122233", password_hash=b"h1"))
    _u2 = Repo.create(Usuario(name="Carol", cpf="99988877766", password_hash=b"h2"))

    achado = Repo.get_by_cpf("00011122233")
    assert achado is not None
    assert achado.get_id() == u1.get_id()
    assert achado.get_name() == "Bob"


def test_list_pagination(user_mods):
    users, repos = user_mods
    Usuario = users.User
    Repo = repos.UserRepository

    # Cria 3 usuários
    created = [
        Repo.create(Usuario(name=f"User{i}", cpf=f"{i:011d}", password_hash=b"x"))
        for i in range(3)
    ]

    # Lista com offset=1 e limit=2 → deve retornar os 2 últimos em ordem de id
    lst = Repo.list(limit=2, offset=1)
    assert len(lst) == 2
    assert [u.get_id() for u in lst] == [created[1].get_id(), created[2].get_id()]


def test_update_user(user_mods):
    users, repos = user_mods
    Usuario = users.User
    Repo = repos.UserRepository

    criado = Repo.create(Usuario(name="Dave", cpf="12312312312", password_hash=b"old", profile_image=None))

    # Guarda o timestamp anterior
    prev_updated_at = criado.get_updated_at()

    # Ajusta os campos pelo DTO e atualiza
    criado.set_name("Dave Atualizado")
    criado.set_password_hash(b"new")
    criado.set_profile_image("/img.png")
    atualizado = Repo.update(criado)

    assert atualizado.get_name() == "Dave Atualizado"
    assert atualizado.get_password_hash() == b"new"
    assert atualizado.get_profile_image() == "/img.png"
    # Deve ter alterado o campo de última atualização
    assert atualizado.get_updated_at() != prev_updated_at


def test_update_without_id_raises(user_mods):
    users, repos = user_mods
    Usuario = users.User
    Repo = repos.UserRepository

    sem_id = Usuario(name="Eve", cpf="55544433322", password_hash=b"pw")
    with pytest.raises(ValueError):
        Repo.update(sem_id)


def test_update_nonexistent_user_raises(user_mods):
    users, repos = user_mods
    Usuario = users.User
    Repo = repos.UserRepository

    fantasma = Usuario(id=999999, name="Ghost", cpf="00000000000", password_hash=b"x")
    with pytest.raises(ValueError):
        Repo.update(fantasma)


def test_duplicate_cpf_now_raises(user_mods):
    """Com UNIQUE no CPF, duplicatas devem levantar erro de negócio."""
    users, repos = user_mods
    Usuario = users.User
    Repo = repos.UserRepository

    _u1 = Repo.create(Usuario(name="Hank", cpf="88877766655", password_hash=b"a"))
    with pytest.raises(ValueError):
        Repo.create(Usuario(name="Ivy", cpf="88877766655", password_hash=b"b"))
