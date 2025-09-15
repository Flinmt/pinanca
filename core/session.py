from __future__ import annotations
import json
import os
from dataclasses import dataclass
from typing import Optional

from core import config
from core.auth import login as auth_login, verify_session, AuthError


def _ensure_dir(path: str) -> None:
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


def _session_path() -> str:
    # Read from env if present to align with runtime-configurable tests
    return os.getenv("SESSION_FILE", config.SESSION_FILE)


def save_token(token: str) -> None:
    path = _session_path()
    _ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"token": token}, f)


def load_token() -> Optional[str]:
    path = _session_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            token = data.get("token")
            return token if isinstance(token, str) and token else None
    except FileNotFoundError:
        return None
    except Exception:
        return None


def clear_token() -> None:
    path = _session_path()
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


def login_and_persist(cpf: str, password: str) -> int:
    """Efetua login e persiste o token localmente. Retorna o user_id."""
    token = auth_login(cpf, password)
    save_token(token)
    payload = verify_session(token)
    return int(payload["sub"])  # user_id


def logout() -> None:
    clear_token()


def current_user() -> Optional["services.users.User"]:
    """Retorna o usuário logado (DTO) ou None se não houver sessão válida.
    Se o token estiver inválido/expirado, limpa o arquivo de sessão.
    """
    from repository.users import UserRepository
    token = load_token()
    if not token:
        return None
    try:
        payload = verify_session(token)
    except AuthError:
        clear_token()
        return None

    uid = int(payload.get("sub", 0))
    if uid <= 0:
        clear_token()
        return None
    return UserRepository.get_by_id(uid)
