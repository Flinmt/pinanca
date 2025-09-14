from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, List

from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from db.session import engine
from db.models import User as UserEntity


# --------- DTO with getters/setters ---------
class User:
    def __init__(
        self,
        id: Optional[int] = None,
        name: str = "",
        cpf: str = "",
        password_hash: bytes = b"",
        profile_image: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self._id = id
        self._name = name
        self._cpf = cpf
        self._password_hash = password_hash
        self._profile_image = profile_image
        self._created_at = created_at
        self._updated_at = updated_at

    # getters
    def get_id(self) -> Optional[int]:
        return self._id

    def get_name(self) -> str:
        return self._name

    def get_cpf(self) -> str:
        return self._cpf

    def get_password_hash(self) -> bytes:
        return self._password_hash

    def get_profile_image(self) -> Optional[str]:
        return self._profile_image

    def get_created_at(self) -> Optional[datetime]:
        return self._created_at

    def get_updated_at(self) -> Optional[datetime]:
        return self._updated_at

    # setters
    def set_name(self, v: str) -> None:
        self._name = v

    def set_cpf(self, v: str) -> None:
        self._cpf = v

    def set_password_hash(self, v: bytes) -> None:
        self._password_hash = v

    def set_profile_image(self, v: Optional[str]) -> None:
        self._profile_image = v

    # conversions
    @staticmethod
    def from_entity(e: UserEntity) -> "User":
        return User(
            id=e.id,
            name=e.name,
            cpf=e.cpf,
            password_hash=e.password_hash,
            profile_image=e.profile_image,
            created_at=e.created_at,
            updated_at=e.updated_at,
        )

    def to_entity(self) -> UserEntity:
        return UserEntity(
            id=self._id,
            name=self._name,
            cpf=self._cpf,
            password_hash=self._password_hash,
            profile_image=self._profile_image,
        )


# --------- Repository (CRUD) ---------
class UserRepository:
    @staticmethod
    def create(model: User) -> User:
        # basic validations
        name = (model.get_name() or "").strip()
        cpf = (model.get_cpf() or "").strip()
        password_hash = model.get_password_hash()

        if not name:
            raise ValueError("Nome é obrigatório")
        if not cpf.isdigit() or len(cpf) != 11:
            raise ValueError("CPF deve conter 11 dígitos numéricos")
        if not isinstance(password_hash, (bytes, bytearray)) or len(password_hash) == 0:
            raise ValueError("Senha hash inválida")

        # proactive duplication check (still trust DB constraint)
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
            return User.from_entity(ent)

    @staticmethod
    def get_by_id(user_id: int) -> Optional[User]:
        with Session(engine) as s:
            ent = s.get(UserEntity, user_id)
            return User.from_entity(ent) if ent else None

    @staticmethod
    def get_by_cpf(cpf: str) -> Optional[User]:
        with Session(engine) as s:
            ent = s.exec(select(UserEntity).where(UserEntity.cpf == cpf)).first()
            return User.from_entity(ent) if ent else None

    @staticmethod
    def list(limit: int = 100, offset: int = 0) -> List[User]:
        with Session(engine) as s:
            q = select(UserEntity).order_by(UserEntity.id).offset(offset).limit(limit)
            return [User.from_entity(e) for e in s.exec(q).all()]

    @staticmethod
    def update(model: User) -> User:
        if model.get_id() is None:
            raise ValueError("ID obrigatório para update")

        with Session(engine) as s:
            ent = s.get(UserEntity, model.get_id())
            if not ent:
                raise ValueError("Usuário não encontrado")

            # apply changes with validation
            new_name = (model.get_name() or "").strip()
            new_cpf = (model.get_cpf() or "").strip()
            new_password = model.get_password_hash()

            if not new_name:
                raise ValueError("Nome é obrigatório")
            if not new_cpf.isdigit() or len(new_cpf) != 11:
                raise ValueError("CPF deve conter 11 dígitos numéricos")
            if not isinstance(new_password, (bytes, bytearray)) or len(new_password) == 0:
                raise ValueError("Senha hash inválida")

            ent.name = new_name
            ent.cpf = new_cpf
            ent.password_hash = bytes(new_password)
            ent.profile_image = model.get_profile_image()
            ent.updated_at = datetime.now(timezone.utc)

            try:
                s.add(ent)
                s.commit()
            except IntegrityError as e:
                s.rollback()
                raise ValueError("CPF já cadastrado ou dados inválidos") from e

            s.refresh(ent)
            return User.from_entity(ent)
