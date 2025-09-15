from __future__ import annotations
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from db.session import engine
from db.models import Transaction as TxEntity, User as UserEntity, Category as CategoryEntity, DebtInstallment as InstallmentEntity

if TYPE_CHECKING:
    from services.transactions import Transaction


ALLOWED_TYPES = {"income", "expense"}
ALLOWED_PERIODICITY = {"none", "monthly", "weekly", "yearly"}


class TransactionRepository:
    @staticmethod
    def _validate_refs(s: Session, model: 'Transaction') -> None:
        if not s.get(UserEntity, int(model.get_user_id())):
            raise ValueError("Usuário não encontrado")
        if model.get_category_id() is not None:
            if not s.get(CategoryEntity, int(model.get_category_id())):
                raise ValueError("Categoria não encontrada")
        if model.get_installment_id() is not None:
            if not s.get(InstallmentEntity, int(model.get_installment_id())):
                raise ValueError("Parcela não encontrada")

    @staticmethod
    def create(model: 'Transaction') -> 'Transaction':
        if model.get_user_id() is None or int(model.get_user_id()) <= 0:
            raise ValueError("Usuário inválido")
        if float(model.get_amount() or 0) <= 0:
            raise ValueError("Valor inválido")
        if (model.get_type() or "").lower() not in ALLOWED_TYPES:
            raise ValueError("Tipo inválido (use 'income' ou 'expense')")
        if (model.get_periodicity() or "none").lower() not in ALLOWED_PERIODICITY:
            raise ValueError("Periodicidade inválida")

        with Session(engine) as s:
            TransactionRepository._validate_refs(s, model)

            ent = model.to_entity()
            s.add(ent)
            try:
                s.commit()
            except IntegrityError as e:
                s.rollback()
                raise ValueError("Dados inválidos ou violação de integridade") from e
            s.refresh(ent)
            from services.transactions import Transaction as DTO
            return DTO.from_entity(ent)

    @staticmethod
    def get_by_id(tx_id: int) -> Optional['Transaction']:
        from services.transactions import Transaction as DTO
        with Session(engine) as s:
            ent = s.get(TxEntity, int(tx_id))
            return DTO.from_entity(ent) if ent else None

    @staticmethod
    def list_by_user(user_id: int, limit: int = 100, offset: int = 0) -> List['Transaction']:
        from services.transactions import Transaction as DTO
        with Session(engine) as s:
            q = (
                select(TxEntity)
                .where(TxEntity.user_id == int(user_id))
                .order_by(TxEntity.occurred_at.desc(), TxEntity.id.desc())
                .offset(offset)
                .limit(limit)
            )
            return [DTO.from_entity(e) for e in s.exec(q).all()]

    @staticmethod
    def list_by_filters(
        user_id: int,
        *,
        type: Optional[str] = None,
        category_id: Optional[int] = None,
        fixed: Optional[bool] = None,
        periodicity: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        installment_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List['Transaction']:
        from services.transactions import Transaction as DTO
        with Session(engine) as s:
            q = select(TxEntity).where(TxEntity.user_id == int(user_id))
            if type is not None:
                t = type.lower()
                if t not in ALLOWED_TYPES:
                    raise ValueError("Tipo inválido (use 'income' ou 'expense')")
                q = q.where(TxEntity.type == t)
            if category_id is not None:
                q = q.where(TxEntity.category_id == int(category_id))
            if fixed is not None:
                q = q.where(TxEntity.fixed == bool(fixed))
            if periodicity is not None:
                p = periodicity.lower()
                if p not in ALLOWED_PERIODICITY:
                    raise ValueError("Periodicidade inválida")
                q = q.where(TxEntity.periodicity == p)
            if start is not None:
                q = q.where(TxEntity.occurred_at >= start)
            if end is not None:
                q = q.where(TxEntity.occurred_at <= end)
            if min_amount is not None:
                q = q.where(TxEntity.amount >= float(min_amount))
            if max_amount is not None:
                q = q.where(TxEntity.amount <= float(max_amount))
            if installment_id is not None:
                q = q.where(TxEntity.installment_id == int(installment_id))
            q = q.order_by(TxEntity.occurred_at.desc(), TxEntity.id.desc()).offset(offset).limit(limit)
            return [DTO.from_entity(e) for e in s.exec(q).all()]

    @staticmethod
    def update(model: 'Transaction') -> 'Transaction':
        from services.transactions import Transaction as DTO
        if model.get_id() is None:
            raise ValueError("ID obrigatório para update")
        if model.get_user_id() is None or int(model.get_user_id()) <= 0:
            raise ValueError("Usuário inválido")
        if float(model.get_amount() or 0) <= 0:
            raise ValueError("Valor inválido")
        if (model.get_type() or "").lower() not in ALLOWED_TYPES:
            raise ValueError("Tipo inválido (use 'income' ou 'expense')")
        if (model.get_periodicity() or "none").lower() not in ALLOWED_PERIODICITY:
            raise ValueError("Periodicidade inválida")

        with Session(engine) as s:
            ent = s.get(TxEntity, model.get_id())
            if not ent:
                raise ValueError("Transação não encontrada")

            TransactionRepository._validate_refs(s, model)

            ent.user_id = int(model.get_user_id())
            ent.category_id = model.get_category_id()
            ent.amount = float(model.get_amount())
            ent.type = model.get_type().lower()
            ent.fixed = bool(model.get_fixed())
            ent.periodicity = (model.get_periodicity() or "none").lower()
            ent.next_execution = model.get_next_execution()
            ent.description = model.get_description()
            ent.notes = model.get_notes()
            ent.occurred_at = model.get_occurred_at() or ent.occurred_at
            ent.installment_id = model.get_installment_id()

            try:
                s.add(ent)
                s.commit()
            except IntegrityError as e:
                s.rollback()
                raise ValueError("Dados inválidos ou violação de integridade") from e

            s.refresh(ent)
            return DTO.from_entity(ent)

    @staticmethod
    def delete(tx_id: int) -> None:
        if tx_id is None or int(tx_id) <= 0:
            raise ValueError("ID inválido")
        with Session(engine) as s:
            ent = s.get(TxEntity, int(tx_id))
            if not ent:
                raise ValueError("Transação não encontrada")
            try:
                s.delete(ent)
                s.commit()
            except IntegrityError as e:
                s.rollback()
                raise ValueError("Transação não pode ser removida pois está em uso") from e

