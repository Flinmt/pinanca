from __future__ import annotations
import base64
import hashlib
import hmac
import json
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

from core import config


class AuthError(ValueError):
    pass


# ---------------- Password hashing (PBKDF2-SHA256) ----------------

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("ascii"))


def hash_password(password: str, *, salt: Optional[bytes] = None, iterations: int = 480_000) -> bytes:
    if not isinstance(password, str) or password == "":
        raise ValueError("Senha inválida")
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, dklen=32)
    enc = f"pbkdf2_sha256${iterations}${_b64url_encode(salt)}${_b64url_encode(dk)}"
    return enc.encode("ascii")


def verify_password(password: str, stored: bytes) -> bool:
    try:
        text = stored.decode("ascii")
    except Exception:
        # Non-ascii legacy raw bytes: fallback to direct compare (insecure, compatibility only)
        return secrets.compare_digest(stored, password.encode("utf-8"))

    if text.startswith("pbkdf2_sha256$"):
        try:
            _alg, iter_s, salt_b64, dk_b64 = text.split("$", 3)
            iterations = int(iter_s)
            salt = _b64url_decode(salt_b64)
            expected = _b64url_decode(dk_b64)
        except Exception:
            return False
        calc = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, dklen=32)
        return hmac.compare_digest(calc, expected)

    # Legacy fallback: direct compare (insecure, compatibility only)
    return secrets.compare_digest(text.encode("utf-8"), password.encode("utf-8"))


# ---------------- Stateless sessions (JWT-like HS256) ----------------

def _sign(data: bytes, secret: str) -> bytes:
    return hmac.new(secret.encode("utf-8"), data, hashlib.sha256).digest()


def issue_session(user_id: int, *, expires_in: Optional[int] = None, now: Optional[datetime] = None) -> str:
    if user_id is None or int(user_id) <= 0:
        raise AuthError("Usuário inválido")
    ttl = int(expires_in if expires_in is not None else config.TOKEN_TTL_SECONDS)
    now_dt = now if now else datetime.now(timezone.utc)
    iat = int(now_dt.timestamp())
    exp = int((now_dt + timedelta(seconds=ttl)).timestamp())

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": int(user_id), "iat": iat, "exp": exp}

    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    signature = _b64url_encode(_sign(signing_input, config.AUTH_SECRET))
    return f"{header_b64}.{payload_b64}.{signature}"


def verify_session(token: str) -> Dict[str, Any]:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        sig = _b64url_decode(signature_b64)
    except Exception as e:
        raise AuthError("Token inválido") from e

    expected = _sign(signing_input, config.AUTH_SECRET)
    if not hmac.compare_digest(sig, expected):
        raise AuthError("Assinatura inválida")

    try:
        payload = json.loads(_b64url_decode(payload_b64))
    except Exception as e:
        raise AuthError("Payload inválido") from e

    now_ts = int(datetime.now(timezone.utc).timestamp())
    if int(payload.get("exp", 0)) < now_ts:
        raise AuthError("Sessão expirada")
    if int(payload.get("sub", 0)) <= 0:
        raise AuthError("Token sem usuário")
    return payload


# ---------------- Login helper ----------------

def login(cpf: str, password: str, *, expires_in: Optional[int] = None) -> str:
    """Autentica com CPF e senha e retorna um token de sessão assinado.
    Lança AuthError em caso de credenciais inválidas.
    """
    from repository.users import UserRepository
    user = UserRepository.get_by_cpf((cpf or "").strip())
    if not user:
        raise AuthError("Credenciais inválidas")

    if not verify_password(password, user.get_password_hash()):
        raise AuthError("Credenciais inválidas")

    return issue_session(user.get_id(), expires_in=expires_in)

