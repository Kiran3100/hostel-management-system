# app/repositories/base.py - COMPLETE FIX

"""Base repository with common CRUD operations - FIXED SOFT DELETE."""

from typing import Generic, TypeVar, Type, Optional, List, Any, Dict
from datetime import datetime, timezone
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with common database operations."""

    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: int) -> Optional[ModelType]:
        """Get a single record by ID."""
        result = await self.db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[ModelType]:
        """Get multiple records with optional filtering."""
        query = select(self.model)

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filtering."""
        query = select(func.count(self.model.id))

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)

        result = await self.db.execute(query)
        return result.scalar() or 0

    async def create(self, obj_in: Dict[str, Any]) -> ModelType:
        """Create a new record."""
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(self, id: int, obj_in: Dict[str, Any]) -> Optional[ModelType]:
        """Update a record."""
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(**obj_in)
            .returning(self.model)
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.scalar_one_or_none()

    async def delete(self, id: int) -> bool:
        """Delete a record (hard delete)."""
        stmt = delete(self.model).where(self.model.id == id)
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0

    async def soft_delete(self, id: int) -> Optional[ModelType]:
        """Soft delete a record (if model supports it)."""
        if not hasattr(self.model, "is_deleted"):
            raise NotImplementedError("Model does not support soft delete")

        # ✅ FIX: Use timezone-aware datetime
        update_data = {
            "is_deleted": True,
            "deleted_at": datetime.now(timezone.utc)
        }

        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(**update_data)
            .returning(self.model)
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.scalar_one_or_none()