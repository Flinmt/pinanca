from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import date, datetime, timezone


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    cpf: str = Field(index=True, unique=True)
    password_hash: bytes
    profile_image: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    name: str


class Responsible(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    name: Optional[str] = None
    related_user_id: Optional[int] = Field(default=None, foreign_key="user.id")


class DebtOrigin(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    name: str


class Debt(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    origin_id: int = Field(foreign_key="debtorigin.id")
    category_id: Optional[int] = Field(default=None, foreign_key="category.id")
    responsible_id: Optional[int] = Field(default=None, foreign_key="responsible.id")
    debt_date: date
    description: Optional[str] = None
    total_amount: float
    installments: int
    notes: Optional[str] = None
    paid: bool = False


class DebtInstallment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    debt_id: int = Field(foreign_key="debt.id")
    number: int
    amount: float
    due_on: date
    paid: bool = False
    paid_at: Optional[datetime] = None


class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    category_id: Optional[int] = Field(default=None, foreign_key="category.id")
    amount: float
    type: str   # 'income' or 'expense'
    fixed: bool = False
    periodicity: str = "none"  # 'none','monthly','weekly','yearly'
    next_execution: Optional[date] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    installment_id: Optional[int] = Field(default=None, foreign_key="debtinstallment.id")
