"""
Admin Router
File: api/v1/routes/admin_route.py

Superadmin-only endpoints for user management, listing management,
support tickets, and dashboard statistics.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.database import get_db
from api.core.dependencies.rbac import require_superadmin
from api.utils.success_response import success_response
from api.v1.models.users import User
from api.v1.schemas.admin import (
    AdminPropertyResponse,
    AdminRideResponse,
    AdminUserResponse,
    ChangeListingStatusRequest,
    ChangeTicketStatusRequest,
    ChangeUserRoleRequest,
    ChangeUserStatusRequest,
    DashboardStatsResponse,
    VerifyVendorRequest,
)
from api.v1.services.admin import admin_service


admin = APIRouter(prefix="/admin", tags=["Admin"])


# ===================================================================
# Dashboard Stats
# ===================================================================


@admin.get(
    "/dashboard/stats",
    status_code=status.HTTP_200_OK,
    summary="Get dashboard statistics",
)
async def dashboard_stats(
    current_user: User = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Return aggregated stats for the admin dashboard."""
    stats = await admin_service.get_dashboard_stats(db)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Dashboard stats retrieved successfully.",
        data=stats,
    )


# ===================================================================
# User Management
# ===================================================================


@admin.get(
    "/users",
    status_code=status.HTTP_200_OK,
    summary="List all users (paginated, searchable)",
)
async def list_users(
    search: Optional[str] = Query(None, description="Search by name, email, or username"),
    role: Optional[str] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    result = await admin_service.list_users(
        db=db, search=search, role=role, is_active=is_active, page=page, limit=limit
    )
    users_data = [
        AdminUserResponse.model_validate(u).model_dump() for u in result["users"]
    ]
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Users retrieved successfully.",
        data={
            "total": result["total"],
            "page": result["page"],
            "limit": result["limit"],
            "users": users_data,
        },
    )


@admin.get(
    "/users/stats",
    status_code=status.HTTP_200_OK,
    summary="Get user stats (counts by role, status)",
)
async def user_stats(
    current_user: User = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    stats = await admin_service.get_user_stats(db)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="User stats retrieved successfully.",
        data=stats,
    )


@admin.get(
    "/users/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Get full user details",
)
async def get_user_detail(
    user_id: str,
    current_user: User = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    user = await admin_service.get_user_detail(user_id, db)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="User details retrieved successfully.",
        data=AdminUserResponse.model_validate(user).model_dump(),
    )


@admin.patch(
    "/users/{user_id}/role",
    status_code=status.HTTP_200_OK,
    summary="Change user role",
)
async def change_user_role(
    user_id: str,
    schema: ChangeUserRoleRequest,
    current_user: User = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    user = await admin_service.change_user_role(
        user_id=user_id, new_role=schema.role, admin_user=current_user, db=db
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message=f"User role updated to '{schema.role}'.",
        data=AdminUserResponse.model_validate(user).model_dump(),
    )


@admin.patch(
    "/users/{user_id}/verify-vendor",
    status_code=status.HTTP_200_OK,
    summary="Approve or reject vendor verification",
)
async def verify_vendor(
    user_id: str,
    schema: VerifyVendorRequest,
    current_user: User = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    user = await admin_service.verify_vendor(
        user_id=user_id,
        action=schema.action,
        reason=schema.reason,
        admin_user=current_user,
        db=db,
    )
    action_msg = "approved" if schema.action == "approve" else "rejected"
    return success_response(
        status_code=status.HTTP_200_OK,
        message=f"Vendor verification {action_msg}.",
        data=AdminUserResponse.model_validate(user).model_dump(),
    )


@admin.patch(
    "/users/{user_id}/status",
    status_code=status.HTTP_200_OK,
    summary="Activate or deactivate a user account",
)
async def change_user_status(
    user_id: str,
    schema: ChangeUserStatusRequest,
    current_user: User = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    user = await admin_service.change_user_status(
        user_id=user_id,
        is_active=schema.is_active,
        admin_user=current_user,
        db=db,
    )
    status_str = "activated" if schema.is_active else "deactivated"
    return success_response(
        status_code=status.HTTP_200_OK,
        message=f"User account {status_str}.",
        data=AdminUserResponse.model_validate(user).model_dump(),
    )


# ===================================================================
# Property Listing Management
# ===================================================================


@admin.get(
    "/listings/properties",
    status_code=status.HTTP_200_OK,
    summary="List all properties",
)
async def list_properties(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    result = await admin_service.list_properties(
        db=db, status_filter=status_filter, search=search, page=page, limit=limit
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Properties retrieved successfully.",
        data=result,
    )


@admin.get(
    "/listings/properties/{property_id}",
    status_code=status.HTTP_200_OK,
    summary="Get single property with owner details",
)
async def get_property_detail(
    property_id: str,
    current_user: User = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    prop = await admin_service.get_property_detail(property_id, db)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Property details retrieved successfully.",
        data=prop,
    )


@admin.patch(
    "/listings/properties/{property_id}/status",
    status_code=status.HTTP_200_OK,
    summary="Change property listing status",
)
async def change_property_status(
    property_id: str,
    schema: ChangeListingStatusRequest,
    current_user: User = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    prop = await admin_service.change_property_status(
        property_id=property_id,
        new_status=schema.status,
        admin_notes=schema.admin_notes,
        admin_user=current_user,
        db=db,
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message=f"Property status updated to '{schema.status}'.",
        data=AdminPropertyResponse.model_validate(prop).model_dump(),
    )


# ===================================================================
# Ride Listing Management
# ===================================================================


@admin.get(
    "/listings/rides",
    status_code=status.HTTP_200_OK,
    summary="List all rides",
)
async def list_rides(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    result = await admin_service.list_rides(
        db=db, status_filter=status_filter, search=search, page=page, limit=limit
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Rides retrieved successfully.",
        data=result,
    )


@admin.get(
    "/listings/rides/{ride_id}",
    status_code=status.HTTP_200_OK,
    summary="Get single ride with owner details",
)
async def get_ride_detail(
    ride_id: str,
    current_user: User = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    ride = await admin_service.get_ride_detail(ride_id, db)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Ride details retrieved successfully.",
        data=ride,
    )


@admin.patch(
    "/listings/rides/{ride_id}/status",
    status_code=status.HTTP_200_OK,
    summary="Change ride listing status",
)
async def change_ride_status(
    ride_id: str,
    schema: ChangeListingStatusRequest,
    current_user: User = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    ride = await admin_service.change_ride_status(
        ride_id=ride_id,
        new_status=schema.status,
        admin_notes=schema.admin_notes,
        admin_user=current_user,
        db=db,
    )
    ride_dict = {
        "id":                       ride.id,
        "user_id":                  ride.user_id,
        "ride_type":                ride.ride_type,
        "seat_count":               ride.seat_count,
        "door_count":               ride.door_count,
        "pickup_location":          ride.pickup_location,
        "pickup_latitude":          ride.pickup_latitude,
        "pickup_longitude":         ride.pickup_longitude,
        "adult_passenger_count":    ride.adult_passenger_count,
        "children_passenger_count": ride.children_passenger_count,
        "infant_passenger_count":   ride.infant_passenger_count,
        "features":                 ride.features or [],
        "price":                    ride.price,
        "currency":                 ride.currency,
        "status":                   ride.status,
        "admin_notes":              ride.admin_notes,
        "created_at":               ride.created_at,
        "updated_at":               ride.updated_at,
        "photos": [m.url for m in (ride.media or []) if m.media_type == "image"],
    }
    return success_response(
        status_code=status.HTTP_200_OK,
        message=f"Ride status updated to '{schema.status}'.",
        data=AdminRideResponse.model_validate(ride_dict).model_dump(),
    )


# ===================================================================
# Support Ticket Management
# ===================================================================


@admin.get(
    "/support/tickets",
    status_code=status.HTTP_200_OK,
    summary="List all support tickets",
)
async def list_tickets(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    result = await admin_service.list_tickets(
        db=db, status_filter=status_filter, page=page, limit=limit
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Tickets retrieved successfully.",
        data=result,
    )


@admin.patch(
    "/support/tickets/{ticket_id}/status",
    status_code=status.HTTP_200_OK,
    summary="Update ticket status",
)
async def change_ticket_status(
    ticket_id: str,
    schema: ChangeTicketStatusRequest,
    current_user: User = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    ticket = await admin_service.change_ticket_status(
        ticket_id=ticket_id,
        new_status=schema.status,
        admin_user=current_user,
        db=db,
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message=f"Ticket status updated to '{schema.status}'.",
        data={
            "id": ticket.id,
            "status": ticket.status,
            "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
        },
    )