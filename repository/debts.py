from __future__ import annotations
from typing import Optional, List, TYPE_CHECKING
from datetime import date

from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from db.session import engine
from db.models import Debt as DebtEntity, User as UserEntity, DebtOrigin as OriginEntity, Category as CategoryEntity, Responsible as ResponsibleEntity

if TYPE_CHECKING:
    from services.debts import Debt


class DebtRepository:
    @staticmethod
    def _validate_foreign_keys(s: Session, model: 'Debt') -> None:
        if not s.get(UserEntity, int(model.get_user_id())):
            raise ValueError("Usuário não encontrado")
        if not s.get(OriginEntity, int(model.get_origin_id())):
            raise ValueError("Origem não encontrada")
        if model.get_category_id() is not None:
            if not s.get(CategoryEntity, int(model.get_category_id())):
                raise ValueError("Categoria não encontrada")
        if model.get_responsible_id() is not None:
            if not s.get(ResponsibleEntity, int(model.get_responsible_id())):
                raise ValueError("Responsável não encontrado")

    @staticmethod
    def create(model: 'Debt') -> 'Debt':
        if model.get_user_id() is None or int(model.get_user_id()) <= 0:
            raise ValueError("Usuário inválido")
        if model.get_origin_id() is None or int(model.get_origin_id()) <= 0:
            raise ValueError("Origem inválida")
        if model.get_debt_date() is None:
            raise ValueError("Data da dívida é obrigatória")
        if float(model.get_total_amount() or 0) <= 0:
            raise ValueError("Valor total inválido")
        if int(model.get_installments() or 0) <= 0:
            raise ValueError("Número de parcelas inválido")

        with Session(engine) as s:
            DebtRepository._validate_foreign_keys(s, model)

            ent = model.to_entity()
            s.add(ent)
            try:
                s.commit()
            except IntegrityError as e:
                s.rollback()
                raise ValueError("Dados inválidos ou violação de integridade") from e
            s.refresh(ent)
            from services.debts import Debt as DTO
            return DTO.from_entity(ent)

    @staticmethod
    def get_by_id(debt_id: int) -> Optional['Debt']:
        from services.debts import Debt as DTO
        with Session(engine) as s:
            ent = s.get(DebtEntity, int(debt_id))
            return DTO.from_entity(ent) if ent else None

    @staticmethod
    def list_by_user(user_id: int, limit: int = 100, offset: int = 0) -> List['Debt']:
        from services.debts import Debt as DTO
        with Session(engine) as s:
            q = (
                select(DebtEntity)
                .where(DebtEntity.user_id == int(user_id))
                .order_by(DebtEntity.id)
                .offset(offset)
                .limit(limit)
            )
            return [DTO.from_entity(e) for e in s.exec(q).all()]

    @staticmethod
    def list_by_user_and_paid(user_id: int, paid: bool, limit: int = 100, offset: int = 0) -> List['Debt']:
        from services.debts import Debt as DTO
        with Session(engine) as s:
            q = (
                select(DebtEntity)
                .where(DebtEntity.user_id == int(user_id), DebtEntity.paid == bool(paid))
                .order_by(DebtEntity.id)
                .offset(offset)
                .limit(limit)
            )
            return [DTO.from_entity(e) for e in s.exec(q).all()]

    @staticmethod
    def list_by_user_and_origin(user_id: int, origin_id: int, limit: int = 100, offset: int = 0) -> List['Debt']:
        from services.debts import Debt as DTO
        with Session(engine) as s:
            q = (
                select(DebtEntity)
                .where(DebtEntity.user_id == int(user_id), DebtEntity.origin_id == int(origin_id))
                .order_by(DebtEntity.id)
                .offset(offset)
                .limit(limit)
            )
            return [DTO.from_entity(e) for e in s.exec(q).all()]

    @staticmethod
    def list_by_user_and_date_range(
        user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List['Debt']:
        """Lista dívidas por usuário filtrando por intervalo de datas (fechado).
        Pelo menos um dos limites (start_date/end_date) deve ser fornecido.
        """
        from services.debts import Debt as DTO
        if start_date is None and end_date is None:
            raise ValueError("Informe start_date e/ou end_date")

        with Session(engine) as s:
            q = select(DebtEntity).where(DebtEntity.user_id == int(user_id))
            if start_date is not None:
                q = q.where(DebtEntity.debt_date >= start_date)
            if end_date is not None:
                q = q.where(DebtEntity.debt_date <= end_date)
            q = q.order_by(DebtEntity.debt_date, DebtEntity.id).offset(offset).limit(limit)
            return [DTO.from_entity(e) for e in s.exec(q).all()]

    @staticmethod
    def list_by_filters(
        user_id: int,
        *,
        paid: Optional[bool] = None,
        origin_id: Optional[int] = None,
        category_id: Optional[int] = None,
        responsible_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        installments_min: Optional[int] = None,
        installments_max: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List['Debt']:
        """Lista dívidas por diversos filtros opcionais.
        Todos os filtros são AND entre si. Ordena por data e id.
        """
        from services.debts import Debt as DTO
        with Session(engine) as s:
            q = select(DebtEntity).where(DebtEntity.user_id == int(user_id))
            if paid is not None:
                q = q.where(DebtEntity.paid == bool(paid))
            if origin_id is not None:
                q = q.where(DebtEntity.origin_id == int(origin_id))
            if category_id is not None:
                q = q.where(DebtEntity.category_id == int(category_id))
            if responsible_id is not None:
                q = q.where(DebtEntity.responsible_id == int(responsible_id))
            if start_date is not None:
                q = q.where(DebtEntity.debt_date >= start_date)
            if end_date is not None:
                q = q.where(DebtEntity.debt_date <= end_date)
            if installments_min is not None:
                q = q.where(DebtEntity.installments >= int(installments_min))
            if installments_max is not None:
                q = q.where(DebtEntity.installments <= int(installments_max))
            q = q.order_by(DebtEntity.debt_date, DebtEntity.id).offset(offset).limit(limit)
            return [DTO.from_entity(e) for e in s.exec(q).all()]

    @staticmethod
    def update(model: 'Debt') -> 'Debt':
        from services.debts import Debt as DTO
        if model.get_id() is None:
            raise ValueError("ID obrigatório para update")
        if model.get_debt_date() is None:
            raise ValueError("Data da dívida é obrigatória")
        if float(model.get_total_amount() or 0) <= 0:
            raise ValueError("Valor total inválido")
        if int(model.get_installments() or 0) <= 0:
            raise ValueError("Número de parcelas inválido")

        with Session(engine) as s:
            ent = s.get(DebtEntity, model.get_id())
            if not ent:
                raise ValueError("Dívida não encontrada")

            if model.get_user_id() is None:
                raise ValueError("Usuário inválido")
            if model.get_origin_id() is None:
                raise ValueError("Origem inválida")
            DebtRepository._validate_foreign_keys(s, model)

            ent.user_id = int(model.get_user_id())
            ent.origin_id = int(model.get_origin_id())
            ent.category_id = model.get_category_id()
            ent.responsible_id = model.get_responsible_id()
            ent.debt_date = model.get_debt_date()
            ent.description = model.get_description()
            ent.total_amount = float(model.get_total_amount())
            ent.installments = int(model.get_installments())
            ent.notes = model.get_notes()
            ent.paid = bool(model.get_paid())

            try:
                s.add(ent)
                s.commit()
            except IntegrityError as e:
                s.rollback()
                raise ValueError("Dados inválidos ou violação de integridade") from e

            s.refresh(ent)
            return DTO.from_entity(ent)

    @staticmethod
    def delete(debt_id: int) -> None:
        if debt_id is None or int(debt_id) <= 0:
            raise ValueError("ID inválido")
        with Session(engine) as s:
            ent = s.get(DebtEntity, int(debt_id))
            if not ent:
                raise ValueError("Dívida não encontrada")
            try:
                s.delete(ent)
                s.commit()
            except IntegrityError as e:
                s.rollback()
                raise ValueError("Dívida não pode ser removida pois está em uso") from e
