from __future__ import annotations
from typing import Optional, List, TYPE_CHECKING

from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from db.session import engine
from db.models import Responsible as ResponsibleEntity, User as UserEntity

if TYPE_CHECKING:
    from services.responsibles import Responsible


class ResponsibleRepository:
    @staticmethod
    def create(model: 'Responsible') -> 'Responsible':
        if model.get_user_id() is None or int(model.get_user_id()) <= 0:
            raise ValueError("Usuário inválido")
        name = model.get_name()
        if name is not None and (name.strip() == ""):
            raise ValueError("Nome do responsável é inválido")

        with Session(engine) as s:
            if not s.get(UserEntity, model.get_user_id()):
                raise ValueError("Usuário não encontrado")
            if model.get_related_user_id() is not None:
                if not s.get(UserEntity, model.get_related_user_id()):
                    raise ValueError("Usuário relacionado não encontrado")

            ent = model.to_entity()
            s.add(ent)
            try:
                s.commit()
            except IntegrityError as e:
                s.rollback()
                raise ValueError("Dados inválidos ou violação de integridade") from e
            s.refresh(ent)
            from services.responsibles import Responsible as DTO
            return DTO.from_entity(ent)

    @staticmethod
    def get_by_id(responsible_id: int) -> Optional['Responsible']:
        from services.responsibles import Responsible as DTO
        with Session(engine) as s:
            ent = s.get(ResponsibleEntity, int(responsible_id))
            return DTO.from_entity(ent) if ent else None

    @staticmethod
    def list_by_user(user_id: int, limit: int = 100, offset: int = 0) -> List['Responsible']:
        from services.responsibles import Responsible as DTO
        with Session(engine) as s:
            q = (
                select(ResponsibleEntity)
                .where(ResponsibleEntity.user_id == user_id)
                .order_by(ResponsibleEntity.id)
                .offset(offset)
                .limit(limit)
            )
            return [DTO.from_entity(e) for e in s.exec(q).all()]

    @staticmethod
    def update(model: 'Responsible') -> 'Responsible':
        from services.responsibles import Responsible as DTO
        if model.get_id() is None:
            raise ValueError("ID obrigatório para update")

        name = model.get_name()
        if name is not None and (name.strip() == ""):
            raise ValueError("Nome do responsável é inválido")
        if model.get_user_id() is None or int(model.get_user_id()) <= 0:
            raise ValueError("Usuário inválido")

        with Session(engine) as s:
            ent = s.get(ResponsibleEntity, model.get_id())
            if not ent:
                raise ValueError("Responsável não encontrado")

            if not s.get(UserEntity, model.get_user_id()):
                raise ValueError("Usuário não encontrado")

            if model.get_related_user_id() is not None:
                if not s.get(UserEntity, model.get_related_user_id()):
                    raise ValueError("Usuário relacionado não encontrado")

            ent.user_id = int(model.get_user_id())
            ent.name = model.get_name()
            ent.related_user_id = model.get_related_user_id()

            try:
                s.add(ent)
                s.commit()
            except IntegrityError as e:
                s.rollback()
                raise ValueError("Dados inválidos ou violação de integridade") from e

            s.refresh(ent)
            return DTO.from_entity(ent)

    @staticmethod
    def delete(responsible_id: int) -> None:
        if responsible_id is None or int(responsible_id) <= 0:
            raise ValueError("ID inválido")

        with Session(engine) as s:
            ent = s.get(ResponsibleEntity, int(responsible_id))
            if not ent:
                raise ValueError("Responsável não encontrado")
            try:
                s.delete(ent)
                s.commit()
            except IntegrityError as e:
                s.rollback()
                raise ValueError("Responsável não pode ser removido pois está em uso") from e

