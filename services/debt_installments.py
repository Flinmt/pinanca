from __future__ import annotations
from typing import Optional
from datetime import date, datetime

from db.models import DebtInstallment as DebtInstallmentEntity


class DebtInstallment:
    def __init__(
        self,
        id: Optional[int] = None,
        debt_id: Optional[int] = None,
        number: int = 1,
        amount: float = 0.0,
        due_on: Optional[date] = None,
        paid: bool = False,
        paid_at: Optional[datetime] = None,
    ):
        self._id = id
        self._debt_id = debt_id
        self._number = number
        self._amount = amount
        self._due_on = due_on
        self._paid = paid
        self._paid_at = paid_at

    # getters
    def get_id(self) -> Optional[int]:
        return self._id

    def get_debt_id(self) -> Optional[int]:
        return self._debt_id

    def get_number(self) -> int:
        return self._number

    def get_amount(self) -> float:
        return self._amount

    def get_due_on(self) -> Optional[date]:
        return self._due_on

    def get_paid(self) -> bool:
        return self._paid

    def get_paid_at(self) -> Optional[datetime]:
        return self._paid_at

    # setters
    def set_debt_id(self, v: int) -> None:
        self._debt_id = v

    def set_number(self, v: int) -> None:
        self._number = v

    def set_amount(self, v: float) -> None:
        self._amount = v

    def set_due_on(self, v: date) -> None:
        self._due_on = v

    def set_paid(self, v: bool) -> None:
        self._paid = v

    def set_paid_at(self, v: Optional[datetime]) -> None:
        self._paid_at = v

    # conversions
    @staticmethod
    def from_entity(e: DebtInstallmentEntity) -> "DebtInstallment":
        return DebtInstallment(
            id=e.id,
            debt_id=e.debt_id,
            number=e.number,
            amount=e.amount,
            due_on=e.due_on,
            paid=e.paid,
            paid_at=e.paid_at,
        )

    def to_entity(self) -> DebtInstallmentEntity:
        return DebtInstallmentEntity(
            id=self._id,
            debt_id=self._debt_id,
            number=self._number,
            amount=self._amount,
            due_on=self._due_on,
            paid=self._paid,
            paid_at=self._paid_at,
        )


# Repository moved to `repository.debt_installments.DebtInstallmentRepository`

