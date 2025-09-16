from __future__ import annotations
import calendar
from typing import Optional
from datetime import date

from db.models import Debt as DebtEntity


class Debt:
    def __init__(
        self,
        id: Optional[int] = None,
        user_id: Optional[int] = None,
        origin_id: Optional[int] = None,
        category_id: Optional[int] = None,
        responsible_id: Optional[int] = None,
        debt_date: Optional[date] = None,
        description: Optional[str] = None,
        total_amount: float = 0.0,
        installments: int = 1,
        notes: Optional[str] = None,
        paid: bool = False,
    ):
        self._id = id
        self._user_id = user_id
        self._origin_id = origin_id
        self._category_id = category_id
        self._responsible_id = responsible_id
        self._debt_date = debt_date
        self._description = description
        self._total_amount = total_amount
        self._installments = installments
        self._notes = notes
        self._paid = paid

    # getters
    def get_id(self) -> Optional[int]: return self._id
    def get_user_id(self) -> Optional[int]: return self._user_id
    def get_origin_id(self) -> Optional[int]: return self._origin_id
    def get_category_id(self) -> Optional[int]: return self._category_id
    def get_responsible_id(self) -> Optional[int]: return self._responsible_id
    def get_debt_date(self) -> Optional[date]: return self._debt_date
    def get_description(self) -> Optional[str]: return self._description
    def get_total_amount(self) -> float: return self._total_amount
    def get_installments(self) -> int: return self._installments
    def get_notes(self) -> Optional[str]: return self._notes
    def get_paid(self) -> bool: return self._paid

    def get_last_installment_date(self) -> Optional[date]:
        start = self.get_debt_date()
        installments = int(self.get_installments() or 0)
        if not start or installments <= 0:
            return None

        month_index = (start.month - 1) + (installments - 1)
        year = start.year + month_index // 12
        month = (month_index % 12) + 1
        day = min(start.day, calendar.monthrange(year, month)[1])
        return date(year, month, day)

    # setters
    def set_user_id(self, v: int) -> None: self._user_id = v
    def set_origin_id(self, v: int) -> None: self._origin_id = v
    def set_category_id(self, v: Optional[int]) -> None: self._category_id = v
    def set_responsible_id(self, v: Optional[int]) -> None: self._responsible_id = v
    def set_debt_date(self, v: date) -> None: self._debt_date = v
    def set_description(self, v: Optional[str]) -> None: self._description = v
    def set_total_amount(self, v: float) -> None: self._total_amount = v
    def set_installments(self, v: int) -> None: self._installments = v
    def set_notes(self, v: Optional[str]) -> None: self._notes = v
    def set_paid(self, v: bool) -> None: self._paid = v

    # conversions
    @staticmethod
    def from_entity(e: DebtEntity) -> "Debt":
        return Debt(
            id=e.id,
            user_id=e.user_id,
            origin_id=e.origin_id,
            category_id=e.category_id,
            responsible_id=e.responsible_id,
            debt_date=e.debt_date,
            description=e.description,
            total_amount=e.total_amount,
            installments=e.installments,
            notes=e.notes,
            paid=e.paid,
        )

    def to_entity(self) -> DebtEntity:
        return DebtEntity(
            id=self._id,
            user_id=self._user_id,
            origin_id=self._origin_id,
            category_id=self._category_id,
            responsible_id=self._responsible_id,
            debt_date=self._debt_date,
            description=self._description,
            total_amount=self._total_amount,
            installments=self._installments,
            notes=self._notes,
            paid=self._paid,
        )


# Repository moved to `repository.debts.DebtRepository`
