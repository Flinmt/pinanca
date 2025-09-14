from __future__ import annotations
from typing import Optional

from db.models import Category as CategoryEntity

class Category:
    def __init__(
        self,
        id: Optional[int] = None,
        user_id: Optional[int] = None,
        name: str = "",
    ):
        self._id = id
        self._user_id = user_id
        self._name = name

    # getters
    def get_id(self) -> Optional[int]:
        return self._id

    def get_user_id(self) -> Optional[int]:
        return self._user_id

    def get_name(self) -> str:
        return self._name

    # setters
    def set_user_id(self, v: int) -> None:
        self._user_id = v

    def set_name(self, v: str) -> None:
        self._name = v

    # conversions
    @staticmethod
    def from_entity(e: CategoryEntity) -> "Category":
        return Category(
            id=e.id,
            user_id=e.user_id,
            name=e.name,
        )

    def to_entity(self) -> CategoryEntity:
        return CategoryEntity(
            id=self._id,
            user_id=self._user_id,
            name=self._name,
        )
