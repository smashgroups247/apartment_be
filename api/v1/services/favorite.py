"""Favorite Service"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from api.v1.models.favorite import Favorite
from api.v1.schemas.favorite import AddFavoriteRequest


class FavoriteService:

    async def get_user_favorites(self, user_id: str, db: AsyncSession, item_type: str = None, page: int = 1, size: int = 10):
        offset = (page - 1) * size

        query = select(Favorite).where(Favorite.user_id == user_id)
        if item_type:
            query = query.where(Favorite.item_type == item_type)

        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()

        result = await db.execute(
            query.order_by(Favorite.created_at.desc()).offset(offset).limit(size)
        )
        favorites = result.scalars().all()

        return {
            "items": favorites,
            "total": total,
            "page": page,
            "size": size,
            "pages": -(-total // size) if total > 0 else 1,
        }

    async def add_favorite(self, user_id: str, payload: AddFavoriteRequest, db: AsyncSession):
        existing = await db.execute(
            select(Favorite).where(
                Favorite.user_id == user_id,
                Favorite.item_type == payload.item_type,
                Favorite.item_id == payload.item_id,
            )
        )
        if existing.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Item already in favorites"
            )

        favorite = Favorite(
            user_id=user_id,
            item_id=payload.item_id,
            item_type=payload.item_type,
            item_name=payload.item_name,
            item_location=payload.item_location,
            item_image=payload.item_image,
            item_rating=payload.item_rating,
            item_price=payload.item_price,
        )
        db.add(favorite)
        await db.commit()
        await db.refresh(favorite)
        return favorite

    async def get_favorite_by_id(self, favorite_id: str, user_id: str, db: AsyncSession):
        result = await db.execute(
            select(Favorite).where(Favorite.id == favorite_id)
        )
        favorite = result.scalars().first()

        if not favorite:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Favorite not found")

        if favorite.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        return favorite

    async def remove_favorite(self, favorite_id: str, user_id: str, db: AsyncSession):
        favorite = await self.get_favorite_by_id(favorite_id, user_id, db)
        await db.delete(favorite)
        await db.commit()

    async def remove_favorite_by_item(self, item_type: str, item_id: str, user_id: str, db: AsyncSession):
        result = await db.execute(
            select(Favorite).where(
                Favorite.user_id == user_id,
                Favorite.item_type == item_type,
                Favorite.item_id == item_id,
            )
        )
        favorite = result.scalars().first()

        if not favorite:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Favorite not found")

        await db.delete(favorite)
        await db.commit()

    async def get_vendor_favorites(self, db: AsyncSession, item_id: str = None, page: int = 1, size: int = 10):
        offset = (page - 1) * size

        query = select(Favorite)
        if item_id:
            query = query.where(Favorite.item_id == item_id)

        count_result = await db.execute(select(func.count()).select_from(query.subquery()))
        total = count_result.scalar()

        result = await db.execute(
            query.order_by(Favorite.created_at.desc()).offset(offset).limit(size)
        )
        favorites = result.scalars().all()

        return {
            "items": favorites,
            "total": total,
            "page": page,
            "size": size,
            "pages": -(-total // size) if total > 0 else 1,
        }

    async def get_admin_favorites(self, db: AsyncSession, user_id: str = None, page: int = 1, size: int = 10):
        offset = (page - 1) * size

        query = select(Favorite)
        if user_id:
            query = query.where(Favorite.user_id == user_id)

        count_result = await db.execute(select(func.count()).select_from(query.subquery()))
        total = count_result.scalar()

        result = await db.execute(
            query.order_by(Favorite.created_at.desc()).offset(offset).limit(size)
        )
        favorites = result.scalars().all()

        return {
            "items": favorites,
            "total": total,
            "page": page,
            "size": size,
            "pages": -(-total // size) if total > 0 else 1,
        }

    async def get_top_favorited(self, db: AsyncSession, limit: int = 10):
        result = await db.execute(
            select(
                Favorite.item_id,
                Favorite.item_name,
                Favorite.item_type,
                func.count(Favorite.item_id).label("count")
            )
            .group_by(Favorite.item_id, Favorite.item_name, Favorite.item_type)
            .order_by(func.count(Favorite.item_id).desc())
            .limit(limit)
        )
        rows = result.all()
        return [
            {
                "item_id": r.item_id,
                "item_name": r.item_name,
                "item_type": r.item_type,
                "count": r.count
            }
            for r in rows
        ]


favorite_service = FavoriteService()