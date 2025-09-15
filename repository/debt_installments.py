from __future__ import annotations
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone

from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from db.session import engine
from db.models import DebtInstallment as InstallmentEntity, Debt as DebtEntity

if TYPE_CHECKING:
    from services.debt_installments import DebtInstallment


class DebtInstallmentRepository:
    @staticmethod
    def create(model: 'DebtInstallment') -> 'DebtInstallment':
        if model.get_debt_id() is None or int(model.get_debt_id()) <= 0:
            raise ValueError("Dívida inválida")
        if model.get_number() is None or int(model.get_number()) <= 0:
            raise ValueError("Número da parcela inválido")
        if model.get_amount() is None or float(model.get_amount()) <= 0:
            raise ValueError("Valor da parcela inválido")
        if model.get_due_on() is None:
            raise ValueError("Data de vencimento é obrigatória")

        with Session(engine) as s:
            if not s.get(DebtEntity, int(model.get_debt_id())):
                raise ValueError("Dívida não encontrada")

            ent = model.to_entity()
            s.add(ent)
            try:
                s.commit()
            except IntegrityError as e:
                s.rollback()
                raise ValueError("Dados inválidos ou violação de integridade") from e
            s.refresh(ent)

            from services.debt_installments import DebtInstallment as DTO
            return DTO.from_entity(ent)

    @staticmethod
    def get_by_id(installment_id: int) -> Optional['DebtInstallment']:
        from services.debt_installments import DebtInstallment as DTO
        with Session(engine) as s:
            ent = s.get(InstallmentEntity, int(installment_id))
            return DTO.from_entity(ent) if ent else None

    @staticmethod
    def list_by_debt(debt_id: int, limit: int = 100, offset: int = 0) -> List['DebtInstallment']:
        from services.debt_installments import DebtInstallment as DTO
        with Session(engine) as s:
            q = (
                select(InstallmentEntity)
                .where(InstallmentEntity.debt_id == int(debt_id))
                .order_by(InstallmentEntity.number)
                .offset(offset)
                .limit(limit)
            )
            return [DTO.from_entity(e) for e in s.exec(q).all()]

    @staticmethod
    def update(model: 'DebtInstallment') -> 'DebtInstallment':
        from services.debt_installments import DebtInstallment as DTO
        if model.get_id() is None:
            raise ValueError("ID obrigatório para update")
        if model.get_number() is None or int(model.get_number()) <= 0:
            raise ValueError("Número da parcela inválido")
        if model.get_amount() is None or float(model.get_amount()) <= 0:
            raise ValueError("Valor da parcela inválido")
        if model.get_due_on() is None:
            raise ValueError("Data de vencimento é obrigatória")

        with Session(engine) as s:
            ent = s.get(InstallmentEntity, model.get_id())
            if not ent:
                raise ValueError("Parcela não encontrada")

            if model.get_debt_id() is None or not s.get(DebtEntity, int(model.get_debt_id())):
                raise ValueError("Dívida não encontrada")

            ent.debt_id = int(model.get_debt_id())
            ent.number = int(model.get_number())
            ent.amount = float(model.get_amount())
            ent.due_on = model.get_due_on()
            ent.paid = bool(model.get_paid())
            # Ajusta paid_at conforme consistência
            if ent.paid:
                ent.paid_at = model.get_paid_at() or datetime.now(timezone.utc)
            else:
                ent.paid_at = None

            try:
                s.add(ent)
                s.commit()
            except IntegrityError as e:
                s.rollback()
                raise ValueError("Dados inválidos ou violação de integridade") from e

            s.refresh(ent)
            return DTO.from_entity(ent)

    @staticmethod
    def delete(installment_id: int) -> None:
        if installment_id is None or int(installment_id) <= 0:
            raise ValueError("ID inválido")

        with Session(engine) as s:
            ent = s.get(InstallmentEntity, int(installment_id))
            if not ent:
                raise ValueError("Parcela não encontrada")
            try:
                s.delete(ent)
                s.commit()
            except IntegrityError as e:
                s.rollback()
                raise ValueError("Parcela não pode ser removida pois está em uso") from e

