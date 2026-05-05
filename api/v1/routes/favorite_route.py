"""Favorites Router"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from api.db.database import get_db
from api.utils.jwt_handler import get_current_user
from api.utils.role_checker import require_role
from api.utils.success_response import success_response
from api.v1.models.users import User
from api.v1.schemas.favorite import AddFavoriteRequest, FavoriteResponse
from api.v1.services.favorite import favorite_service

favorites = APIRouter(prefix="/favorites", tags=["Favorites"])


# ─── User Endpoints ───────────────────────────────────────────────────────────

@favorites.get("", status_code=status.HTTP_200_OK)
async def get_favorites(
    item_type: Optional[str] = Query(None, pattern="^(stay|car_rental)$"),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await favorite_service.get_user_favorites(
        user_id=current_user.id, db=db, item_type=item_type, page=page, size=size
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Favorites retrieved successfully.",
        data=data,
    )


@favorites.post("", status_code=status.HTTP_201_CREATED)
async def add_favorite(
    payload: AddFavoriteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await favorite_service.add_favorite(
        user_id=current_user.id, payload=payload, db=db
    )
    return success_response(
        status_code=status.HTTP_201_CREATED,
        message="Item added to favorites successfully.",
        data=FavoriteResponse.model_validate(data).model_dump(),
    )


@favorites.get("/count", status_code=status.HTTP_200_OK)
async def get_favorites_count(
    item_type: Optional[str] = Query(None, pattern="^(stay|car_rental)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await favorite_service.get_user_favorites(
        user_id=current_user.id, db=db, item_type=item_type, page=1, size=1
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Favorites count retrieved successfully.",
        data={"count": data["total"]},
    )


@favorites.delete("/remove/{item_type}/{item_id}", status_code=status.HTTP_200_OK)
async def remove_favorite_by_item(
    item_type: str,
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await favorite_service.remove_favorite_by_item(
        item_type=item_type, item_id=item_id, user_id=current_user.id, db=db
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Item removed from favorites successfully.",
        data=None,
    )


# ─── Vendor Endpoints ─────────────────────────────────────────────────────────

@favorites.get("/vendor/listings", status_code=status.HTTP_200_OK)
async def get_vendor_favorites(
    item_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(require_role("vendor", "admin")),
    db: AsyncSession = Depends(get_db),
):
    data = await favorite_service.get_vendor_favorites(
        db=db, item_id=item_id, page=page, size=size
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Vendor favorites retrieved successfully.",
        data=data,
    )


# ─── Admin Endpoints ──────────────────────────────────────────────────────────

@favorites.get("/admin/all", status_code=status.HTTP_200_OK)
async def get_admin_favorites(
    user_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    data = await favorite_service.get_admin_favorites(
        db=db, user_id=user_id, page=page, size=size
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="All favorites retrieved successfully.",
        data=data,
    )


@favorites.get("/admin/top", status_code=status.HTTP_200_OK)
async def get_top_favorited(
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    data = await favorite_service.get_top_favorited(db=db, limit=limit)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Top favorited items retrieved successfully.",
        data=data,
    )


@favorites.get("/admin/user/{user_id}", status_code=status.HTTP_200_OK)
async def get_admin_favorites_by_user(
    user_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    data = await favorite_service.get_admin_favorites(
        db=db, user_id=user_id, page=page, size=size
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message=f"Favorites for user {user_id} retrieved successfully.",
        data=data,
    )


# ─── Must be last to avoid catching other routes ──────────────────────────────

@favorites.get("/{favorite_id}", status_code=status.HTTP_200_OK)
async def get_favorite(
    favorite_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await favorite_service.get_favorite_by_id(
        favorite_id=favorite_id, user_id=current_user.id, db=db
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Favorite retrieved successfully.",
        data=FavoriteResponse.model_validate(data).model_dump(),
    )


@favorites.delete("/{favorite_id}", status_code=status.HTTP_200_OK)
async def remove_favorite(
    favorite_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await favorite_service.remove_favorite(
        favorite_id=favorite_id, user_id=current_user.id, db=db
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Item removed from favorites successfully.",
        data=None,
    )