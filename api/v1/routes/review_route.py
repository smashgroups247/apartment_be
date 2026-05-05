from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from api.db.database import get_db
from api.utils.jwt_handler import get_current_user
from api.utils.success_response import success_response
from api.v1.models.users import User
from api.v1.schemas.review import CreateReviewRequest, ReviewResponse
from api.v1.services.review import review_service


review = APIRouter(prefix="/reviews", tags=["Reviews"])


@review.post("", status_code=status.HTTP_201_CREATED)
async def create_review(
    schema: CreateReviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await review_service.create_review(
        schema=schema, user_id=current_user.id, db=db
    )
    return success_response(
        status_code=status.HTTP_201_CREATED,
        message="Review submitted successfully.",
        data=ReviewResponse.model_validate(data).model_dump(),
    )


@review.get("", status_code=status.HTTP_200_OK)
async def get_reviews(
    booking_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await review_service.get_user_reviews(
        user_id=current_user.id, db=db, booking_type=booking_type
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Reviews retrieved successfully.",
        data=[ReviewResponse.model_validate(r).model_dump() for r in data],
    )