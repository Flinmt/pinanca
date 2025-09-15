from __future__ import annotations
from typing import Optional, List, TYPE_CHECKING

from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from db.session import engine
from db.models import DebtOrigin as DebtOriginEntity, User as UserEntity

if TYPE_CHECKING:
    from services.debt_origins import DebtOrigin


class DebtOriginRepository:
    @staticmethod
    def create(model: 'DebtOrigin') -> 'DebtOrigin':
        if model.get_user_id() is None or int(model.get_user_id()) <= 0:
            raise ValueError("Usuário inválido")
        name = (model.get_name() or "").strip()
        if not name:
            raise ValueError("Nome da origem é obrigatório")

        with Session(engine) as s:
            if not s.get(UserEntity, model.get_user_id()):
                raise ValueError("Usuário não encontrado")

            ent = model.to_entity()
            s.add(ent)
            try:
                s.commit()
            except IntegrityError as e:
                s.rollback()
                raise ValueError("Dados inválidos ou violação de integridade") from e
            s.refresh(ent)

            from services.debt_origins import DebtOrigin as DTO
            return DTO.from_entity(ent)

    @staticmethod
    def get_by_id(origin_id: int) -> Optional['DebtOrigin']:
        from services.debt_origins import DebtOrigin as DTO
        with Session(engine) as s:
            ent = s.get(DebtOriginEntity, int(origin_id))
            return DTO.from_entity(ent) if ent else None

    @staticmethod
    def list_by_user(user_id: int, limit: int = 100, offset: int = 0) -> List['DebtOrigin']:
        from services.debt_origins import DebtOrigin as DTO
        with Session(engine) as s:
            q = (
                select(DebtOriginEntity)
                .where(DebtOriginEntity.user_id == user_id)
                .order_by(DebtOriginEntity.id)
                .offset(offset)
                .limit(limit)
            )
            return [DTO.from_entity(e) for e in s.exec(q).all()]

    @staticmethod
    def update(model: 'DebtOrigin') -> 'DebtOrigin':
        from services.debt_origins import DebtOrigin as DTO
        if model.get_id() is None:
            raise ValueError("ID obrigatório para update")

        new_name = (model.get_name() or "").strip()
        if not new_name:
            raise ValueError("Nome da origem é obrigatório")
        if model.get_user_id() is None or int(model.get_user_id()) <= 0:
            raise ValueError("Usuário inválido")

        with Session(engine) as s:
            ent = s.get(DebtOriginEntity, model.get_id())
            if not ent:
                raise ValueError("Origem não encontrada")

            if not s.get(UserEntity, model.get_user_id()):
                raise ValueError("Usuário não encontrado")

            ent.user_id = int(model.get_user_id())
            ent.name = new_name

            try:
                s.add(ent)
                s.commit()
            except IntegrityError as e:
                s.rollback()
                raise ValueError("Dados inválidos ou violação de integridade") from e

            s.refresh(ent)
            return DTO.from_entity(ent)

    @staticmethod
    def delete(origin_id: int) -> None:
        if origin_id is None or int(origin_id) <= 0:
            raise ValueError("ID inválido")

        with Session(engine) as s:
            ent = s.get(DebtOriginEntity, int(origin_id))
            if not ent:
                raise ValueError("Origem não encontrada")
            try:
                s.delete(ent)
                s.commit()
            except IntegrityError as e:
                s.rollback()
                raise ValueError("Origem não pode ser removida pois está em uso") from e

