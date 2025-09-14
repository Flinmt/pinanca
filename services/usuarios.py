# services/usuarios_getset.py
from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from db.session import engine
from db.models import Usuario as UsuarioEntity

# --------- DTO com getters/setters ---------
class Usuario:
    def __init__(
        self,
        id: Optional[int] = None,
        nome: str = "",
        cpf: str = "",
        senha_hash: bytes = b"",
        imagem_perfil: Optional[str] = None,
        data_registro: Optional[datetime] = None,
        data_ultima_atualizacao: Optional[datetime] = None,
    ):
        self._id = id
        self._nome = nome
        self._cpf = cpf
        self._senha_hash = senha_hash
        self._imagem_perfil = imagem_perfil
        self._data_registro = data_registro
        self._data_ultima_atualizacao = data_ultima_atualizacao

    # getters
    def get_id(self) -> Optional[int]: return self._id
    def get_nome(self) -> str: return self._nome
    def get_cpf(self) -> str: return self._cpf
    def get_senha_hash(self) -> bytes: return self._senha_hash
    def get_imagem_perfil(self) -> Optional[str]: return self._imagem_perfil
    def get_data_registro(self) -> Optional[datetime]: return self._data_registro
    def get_data_ultima_atualizacao(self) -> Optional[datetime]: return self._data_ultima_atualizacao

    # setters
    def set_nome(self, v: str) -> None: self._nome = v
    def set_cpf(self, v: str) -> None: self._cpf = v
    def set_senha_hash(self, v: bytes) -> None: self._senha_hash = v
    def set_imagem_perfil(self, v: Optional[str]) -> None: self._imagem_perfil = v

    # conversões
    @staticmethod
    def from_entity(e: UsuarioEntity) -> "Usuario":
        return Usuario(
            id=e.id,
            nome=e.nome,
            cpf=e.cpf,
            senha_hash=e.senha_hash,
            imagem_perfil=e.imagem_perfil,
            data_registro=e.data_registro,
            data_ultima_atualizacao=e.data_ultima_atualizacao,
        )

    def to_entity(self) -> UsuarioEntity:
        return UsuarioEntity(
            id=self._id,
            nome=self._nome,
            cpf=self._cpf,
            senha_hash=self._senha_hash,
            imagem_perfil=self._imagem_perfil,
            data_registro=self._data_registro or datetime.now(datetime.UTC),
            data_ultima_atualizacao=self._data_ultima_atualizacao or datetime.now(datetime.UTC),
        )


# --------- Repositório (CRUD) ---------
class UsuarioRepository:
    @staticmethod
    def create(model: Usuario) -> Usuario:
        ent = model.to_entity()
        with Session(engine) as s:
            s.add(ent)
            try:
                s.commit()
            except IntegrityError as e:
                s.rollback()
                raise ValueError("CPF já cadastrado ou dados inválidos") from e
            s.refresh(ent)
            return Usuario.from_entity(ent)

    @staticmethod
    def get_by_id(user_id: int) -> Optional[Usuario]:
        with Session(engine) as s:
            ent = s.get(UsuarioEntity, user_id)
            return Usuario.from_entity(ent) if ent else None

    @staticmethod
    def get_by_cpf(cpf: str) -> Optional[Usuario]:
        with Session(engine) as s:
            ent = s.exec(select(UsuarioEntity).where(UsuarioEntity.cpf == cpf)).first()
            return Usuario.from_entity(ent) if ent else None

    @staticmethod
    def list(limit: int = 100, offset: int = 0) -> List[Usuario]:
        with Session(engine) as s:
            q = select(UsuarioEntity).order_by(UsuarioEntity.id).offset(offset).limit(limit)
            return [Usuario.from_entity(e) for e in s.exec(q).all()]

    @staticmethod
    def update(model: Usuario) -> Usuario:
        if model.get_id() is None:
            raise ValueError("ID obrigatório para update")

        with Session(engine) as s:
            ent = s.get(UsuarioEntity, model.get_id())
            if not ent:
                raise ValueError("Usuário não encontrado")

            # aplica mudanças
            ent.nome = model.get_nome()
            ent.cpf = model.get_cpf()
            ent.senha_hash = model.get_senha_hash()
            ent.imagem_perfil = model.get_imagem_perfil()
            ent.data_ultima_atualizacao = datetime.utcnow()

            try:
                s.add(ent)
                s.commit()
            except IntegrityError as e:
                s.rollback()
                raise ValueError("CPF já cadastrado ou dados inválidos") from e

            s.refresh(ent)
            return Usuario.from_entity(ent)
