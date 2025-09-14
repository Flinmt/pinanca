from __future__ import annotations
from typing import Optional

from db.models import Responsible as ResponsibleEntity


class Responsible:
    def __init__(
        self,
        id: Optional[int] = None,
        user_id: Optional[int] = None,
        name: Optional[str] = None,
        related_user_id: Optional[int] = None,
    ):
        self._id = id
        self._user_id = user_id
        self._name = name
        self._related_user_id = related_user_id

    # getters
    def get_id(self) -> Optional[int]:
        return self._id

    def get_user_id(self) -> Optional[int]:
        return self._user_id

    def get_name(self) -> Optional[str]:
        return self._name

    def get_related_user_id(self) -> Optional[int]:
        return self._related_user_id

    # setters
    def set_user_id(self, v: int) -> None:
        self._user_id = v

    def set_name(self, v: Optional[str]) -> None:
        self._name = v

    def set_related_user_id(self, v: Optional[int]) -> None:
        self._related_user_id = v

    # conversions
    @staticmethod
    def from_entity(e: ResponsibleEntity) -> "Responsible":
        return Responsible(
            id=e.id,
            user_id=e.user_id,
            name=e.name,
            related_user_id=e.related_user_id,
        )

    def to_entity(self) -> ResponsibleEntity:
        return ResponsibleEntity(
            id=self._id,
            user_id=self._user_id,
            name=self._name,
            related_user_id=self._related_user_id,
        )


# Repository moved to `repository.responsibles.ResponsibleRepository`

