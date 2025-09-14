# init_db.py
from db.session import init_db
import db.models

if __name__ == "__main__":
    init_db()
    print("Banco SQLite criado e tabelas geradas.")

