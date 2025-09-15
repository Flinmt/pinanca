#!/usr/bin/env python3
from __future__ import annotations
import argparse
import getpass
import os
import sys
from pathlib import Path

# Ensure project root on sys.path when running from scripts/
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Default DB_PATH to project data/ if not provided
os.environ.setdefault("DB_PATH", str(ROOT / "data" / "app.db"))

from db.session import init_db
from services.users import User
from repository.users import UserRepository
from core.auth import hash_password


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a new user")
    parser.add_argument("--name", required=False, help="User name")
    parser.add_argument("--cpf", required=False, help="CPF (11 digits)")
    parser.add_argument("--password", required=False, help="Password (if omitted, will prompt)")
    args = parser.parse_args()

    name = args.name or input("Name: ").strip()
    cpf = args.cpf or input("CPF (11 digits): ").strip()
    pwd = args.password or getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm password: ") if not args.password else args.password

    if not name:
        print("Name is required", flush=True)
        return 1
    cpf_digits = ''.join(ch for ch in cpf if ch.isdigit())
    if len(cpf_digits) != 11:
        print("CPF must have 11 digits", flush=True)
        return 1
    if not pwd:
        print("Password is required", flush=True)
        return 1
    if pwd != confirm:
        print("Passwords do not match", flush=True)
        return 1

    init_db()
    try:
        hashed = hash_password(pwd)
        created = UserRepository.create(User(name=name, cpf=cpf_digits, password_hash=hashed))
        print(f"User created with id={created.get_id()}")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
