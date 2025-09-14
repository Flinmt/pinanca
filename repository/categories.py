from __future__ import annotations
from typing import Optional, List, TYPE_CHECKING

from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from db.session import engine
from db.models import Category as CategoryEntity, User as UserEntity

if TYPE_CHECKING:
    from services.categories import Category


class CategoryRepository:
    @staticmethod
    def create(model: 'Category') -> 'Category':
        if model.get_user_id() is None or int(model.get_user_id()) <= 0:
            raise ValueError("Usuário inválido")
        name = (model.get_name() or "").strip()
        if not name:
            raise ValueError("Nome da categoria é obrigatório")

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

            from services.categories import Category as CategoryDTO
            return CategoryDTO.from_entity(ent)

    @staticmethod
    def get_by_id(category_id: int) -> Optional['Category']:
        from services.categories import Category as CategoryDTO
        with Session(engine) as s:
            ent = s.get(CategoryEntity, category_id)
            return CategoryDTO.from_entity(ent) if ent else None

    @staticmethod
    def list_by_user(user_id: int, limit: int = 100, offset: int = 0) -> List['Category']:
        from services.categories import Category as CategoryDTO
        with Session(engine) as s:
            q = (
                select(CategoryEntity)
                .where(CategoryEntity.user_id == user_id)
                .order_by(CategoryEntity.id)
                .offset(offset)
                .limit(limit)
            )
            return [CategoryDTO.from_entity(e) for e in s.exec(q).all()]

    @staticmethod
    def update(model: 'Category') -> 'Category':
        from services.categories import Category as CategoryDTO
        if model.get_id() is None:
            raise ValueError("ID obrigatório para update")

        new_name = (model.get_name() or "").strip()
        if not new_name:
            raise ValueError("Nome da categoria é obrigatório")
        if model.get_user_id() is None or int(model.get_user_id()) <= 0:
            raise ValueError("Usuário inválido")

        with Session(engine) as s:
            ent = s.get(CategoryEntity, model.get_id())
            if not ent:
                raise ValueError("Categoria não encontrada")

            if not s.get(UserEntity, model.get_user_id()):
                raise ValueError("Usuário não encontrado")

            ent.name = new_name
            ent.user_id = int(model.get_user_id())

            try:
                s.add(ent)
                s.commit()
            except IntegrityError as e:
                s.rollback()
                raise ValueError("Dados inválidos ou violação de integridade") from e

            s.refresh(ent)
            return CategoryDTO.from_entity(ent)

