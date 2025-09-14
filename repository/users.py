from __future__ import annotations
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone

from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from db.session import engine
from db.models import User as UserEntity

if TYPE_CHECKING:
    from services.users import User


class UserRepository:
    @staticmethod
    def create(model: 'User') -> 'User':
        name = (model.get_name() or "").strip()
        cpf = (model.get_cpf() or "").strip()
        password_hash = model.get_password_hash()

        if not name:
            raise ValueError("Nome é obrigatório")
        if not cpf.isdigit() or len(cpf) != 11:
            raise ValueError("CPF deve conter 11 dígitos numéricos")
        if not isinstance(password_hash, (bytes, bytearray)) or len(password_hash) == 0:
            raise ValueError("Senha hash inválida")

        with Session(engine) as s:
            exists = s.exec(select(UserEntity.id).where(UserEntity.cpf == cpf)).first()
            if exists:
                raise ValueError("CPF já cadastrado")

        ent = model.to_entity()
        with Session(engine) as s:
            s.add(ent)
            try:
                s.commit()
            except IntegrityError as e:
                s.rollback()
                raise ValueError("CPF já cadastrado ou dados inválidos") from e
            s.refresh(ent)
            from services.users import User as UserDTO
            return UserDTO.from_entity(ent)

    @staticmethod
    def get_by_id(user_id: int) -> Optional['User']:
        from services.users import User as UserDTO
        with Session(engine) as s:
            ent = s.get(UserEntity, user_id)
            return UserDTO.from_entity(ent) if ent else None

    @staticmethod
    def get_by_cpf(cpf: str) -> Optional['User']:
        from services.users import User as UserDTO
        with Session(engine) as s:
            ent = s.exec(select(UserEntity).where(UserEntity.cpf == cpf)).first()
            return UserDTO.from_entity(ent) if ent else None

    @staticmethod
    def list(limit: int = 100, offset: int = 0) -> List['User']:
        from services.users import User as UserDTO
        with Session(engine) as s:
            q = select(UserEntity).order_by(UserEntity.id).offset(offset).limit(limit)
            return [UserDTO.from_entity(e) for e in s.exec(q).all()]

    @staticmethod
    def update(model: 'User') -> 'User':
        from services.users import User as UserDTO
        if model.get_id() is None:
            raise ValueError("ID obrigatório para update")

        with Session(engine) as s:
            ent = s.get(UserEntity, model.get_id())
            if not ent:
                raise ValueError("Usuário não encontrado")

            new_name = (model.get_name() or "").strip()
            new_cpf = (model.get_cpf() or "").strip()

            if not new_name:
                raise ValueError("Nome é obrigatório")
            if not new_cpf.isdigit() or len(new_cpf) != 11:
                raise ValueError("CPF deve conter 11 dígitos numéricos")

            ent.name = new_name
            ent.cpf = new_cpf
            # Password updates are not allowed via this method; keep existing hash
            ent.profile_image = model.get_profile_image()
            ent.updated_at = datetime.now(timezone.utc)

            try:
                s.add(ent)
                s.commit()
            except IntegrityError as e:
                s.rollback()
                raise ValueError("CPF já cadastrado ou dados inválidos") from e

            s.refresh(ent)
            return UserDTO.from_entity(ent)
