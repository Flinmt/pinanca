from __future__ import annotations
from typing import Optional
from datetime import datetime, date

from db.models import Transaction as TransactionEntity


class Transaction:
    def __init__(
        self,
        id: Optional[int] = None,
        user_id: Optional[int] = None,
        category_id: Optional[int] = None,
        amount: float = 0.0,
        type: str = "income",  # 'income' or 'expense'
        fixed: bool = False,
        periodicity: str = "none",  # 'none','monthly','weekly','yearly'
        next_execution: Optional[date] = None,
        description: Optional[str] = None,
        notes: Optional[str] = None,
        occurred_at: Optional[datetime] = None,
        installment_id: Optional[int] = None,
    ):
        self._id = id
        self._user_id = user_id
        self._category_id = category_id
        self._amount = amount
        self._type = type
        self._fixed = fixed
        self._periodicity = periodicity
        self._next_execution = next_execution
        self._description = description
        self._notes = notes
        self._occurred_at = occurred_at
        self._installment_id = installment_id

    # getters
    def get_id(self) -> Optional[int]: return self._id
    def get_user_id(self) -> Optional[int]: return self._user_id
    def get_category_id(self) -> Optional[int]: return self._category_id
    def get_amount(self) -> float: return self._amount
    def get_type(self) -> str: return self._type
    def get_fixed(self) -> bool: return self._fixed
    def get_periodicity(self) -> str: return self._periodicity
    def get_next_execution(self) -> Optional[date]: return self._next_execution
    def get_description(self) -> Optional[str]: return self._description
    def get_notes(self) -> Optional[str]: return self._notes
    def get_occurred_at(self) -> Optional[datetime]: return self._occurred_at
    def get_installment_id(self) -> Optional[int]: return self._installment_id

    # setters
    def set_user_id(self, v: int) -> None: self._user_id = v
    def set_category_id(self, v: Optional[int]) -> None: self._category_id = v
    def set_amount(self, v: float) -> None: self._amount = v
    def set_type(self, v: str) -> None: self._type = v
    def set_fixed(self, v: bool) -> None: self._fixed = v
    def set_periodicity(self, v: str) -> None: self._periodicity = v
    def set_next_execution(self, v: Optional[date]) -> None: self._next_execution = v
    def set_description(self, v: Optional[str]) -> None: self._description = v
    def set_notes(self, v: Optional[str]) -> None: self._notes = v
    def set_occurred_at(self, v: Optional[datetime]) -> None: self._occurred_at = v
    def set_installment_id(self, v: Optional[int]) -> None: self._installment_id = v

    # conversions
    @staticmethod
    def from_entity(e: TransactionEntity) -> "Transaction":
        return Transaction(
            id=e.id,
            user_id=e.user_id,
            category_id=e.category_id,
            amount=e.amount,
            type=e.type,
            fixed=e.fixed,
            periodicity=e.periodicity,
            next_execution=e.next_execution,
            description=e.description,
            notes=e.notes,
            occurred_at=e.occurred_at,
            installment_id=e.installment_id,
        )

    def to_entity(self) -> TransactionEntity:
        return TransactionEntity(
            id=self._id,
            user_id=self._user_id,
            category_id=self._category_id,
            amount=self._amount,
            type=self._type,
            fixed=self._fixed,
            periodicity=self._periodicity,
            next_execution=self._next_execution,
            description=self._description,
            notes=self._notes,
            occurred_at=self._occurred_at,
            installment_id=self._installment_id,
        )


# Repository moved to `repository.transactions.TransactionRepository`

