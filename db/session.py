from sqlmodel import SQLModel, create_engine
import os

DB_PATH = os.getenv("DB_PATH", "./data/app.db")

# cria engine apontando para SQLite
engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False}
)

def init_db():
    # cria tabelas se não existirem
    SQLModel.metadata.create_all(engine)
