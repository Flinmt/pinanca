from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional

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
