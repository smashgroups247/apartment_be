"""
Admin Service
File: api/v1/services/admin.py

Business logic for all superadmin operations.
"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from api.loggers.app_logger import app_logger
from api.v1.models.users import User
from api.v1.models.property import Property
from api.v1.models.rides import Ride, RideStatus
from api.v1.models.support_ticket import SupportTicket


class AdminService:
    """Service layer for superadmin dashboard operations."""

    # -------------------------------------------------------------------
    # Dashboard Stats
    # -------------------------------------------------------------------

    async def get_dashboard_stats(self, db: AsyncSession) -> dict:
        """Return aggregated counts for the admin dashboard."""

        # Users
        total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
        total_vendors = (
            await db.execute(
                select(func.count(User.id)).filter(User.role == "vendor")
            )
        ).scalar() or 0
        total_superadmins = (
            await db.execute(
                select(func.count(User.id)).filter(User.role == "superadmin")
            )
        ).scalar() or 0
        verified_vendors = (
            await db.execute(
                select(func.count(User.id)).filter(
                    User.role == "vendor", User.vendor_verified == True
                )
            )
        ).scalar() or 0
        pending_vendor_verifications = (
            await db.execute(
                select(func.count(User.id)).filter(
                    User.role == "vendor", User.vendor_verified == False
                )
            )
        ).scalar() or 0

        # Properties
        total_properties = (
            await db.execute(select(func.count(Property.id)))
        ).scalar() or 0
        active_properties = (
            await db.execute(
                select(func.count(Property.id)).filter(Property.status == "active")
            )
        ).scalar() or 0
        pending_properties = (
            await db.execute(
                select(func.count(Property.id)).filter(
                    Property.status == "pending_approval"
                )
            )
        ).scalar() or 0

        # Rides
        total_rides = (
            await db.execute(select(func.count(Ride.id)))
        ).scalar() or 0
        published_rides = (
            await db.execute(
                select(func.count(Ride.id)).filter(
                    Ride.status == RideStatus.published
                )
            )
        ).scalar() or 0
        pending_rides = (
            await db.execute(
                select(func.count(Ride.id)).filter(Ride.status == "pending_approval")
            )
        ).scalar() or 0

        # Tickets
        total_tickets = (
            await db.execute(select(func.count(SupportTicket.id)))
        ).scalar() or 0
        open_tickets = (
            await db.execute(
                select(func.count(SupportTicket.id)).filter(
                    SupportTicket.status == "open"
                )
            )
        ).scalar() or 0

        return {
            "total_users": total_users,
            "total_vendors": total_vendors,
            "total_superadmins": total_superadmins,
            "verified_vendors": verified_vendors,
            "pending_vendor_verifications": pending_vendor_verifications,
            "total_properties": total_properties,
            "active_properties": active_properties,
            "pending_properties": pending_properties,
            "total_rides": total_rides,
            "published_rides": published_rides,
            "pending_rides": pending_rides,
            "total_tickets": total_tickets,
            "open_tickets": open_tickets,
        }

    # -------------------------------------------------------------------
    # User Management
    # -------------------------------------------------------------------

    async def list_users(
        self,
        db: AsyncSession,
        search: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        """List all users with optional filters and pagination."""
        query = select(User)

        if search:
            search_term = f"%{search.lower()}%"
            query = query.filter(
                (User.email.ilike(search_term))
                | (User.first_name.ilike(search_term))
                | (User.last_name.ilike(search_term))
                | (User.username.ilike(search_term))
            )

        if role:
            query = query.filter(User.role == role.lower())

        if is_active is not None:
            query = query.filter(User.is_active == is_active)

        # Total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar() or 0

        # Paginate
        offset = (page - 1) * limit
        query = query.order_by(User.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        users = result.scalars().all()

        return {
            "total": total,
            "page": page,
            "limit": limit,
            "users": users,
        }

    async def get_user_detail(self, user_id: str, db: AsyncSession) -> User:
        """Fetch full user details by ID."""
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
            )
        return user

    async def change_user_role(
        self, user_id: str, new_role: str, admin_user: User, db: AsyncSession
    ) -> User:
        """Change a user's role."""
        user = await self.get_user_detail(user_id, db)

        if user.id == admin_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot change your own role.",
            )

        old_role = user.role
        user.role = new_role

        # If demoting from vendor, reset vendor fields
        if new_role == "user":
            user.vendor_verified = False
            user.vendor_verified_at = None

        await db.commit()
        await db.refresh(user)

        app_logger.info(
            f"Admin {admin_user.email} changed user {user.email} role: {old_role} -> {new_role}"
        )
        return user

    async def verify_vendor(
        self,
        user_id: str,
        action: str,
        reason: Optional[str],
        admin_user: User,
        db: AsyncSession,
    ) -> User:
        """Approve or reject vendor verification."""
        user = await self.get_user_detail(user_id, db)

        if user.role != "vendor":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not a vendor.",
            )

        if action == "approve":
            user.vendor_verified = True
            user.vendor_verified_at = datetime.now(tz=timezone.utc)
            user.id_verification_status = "approved"
            app_logger.info(
                f"Admin {admin_user.email} approved vendor verification for {user.email}"
            )
        else:
            user.vendor_verified = False
            user.vendor_verified_at = None
            user.id_verification_status = "rejected"
            app_logger.info(
                f"Admin {admin_user.email} rejected vendor verification for {user.email}: {reason}"
            )

        await db.commit()
        await db.refresh(user)
        return user

    async def change_user_status(
        self, user_id: str, is_active: bool, admin_user: User, db: AsyncSession
    ) -> User:
        """Activate or deactivate a user account."""
        user = await self.get_user_detail(user_id, db)

        if user.id == admin_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot deactivate your own account.",
            )

        user.is_active = is_active
        await db.commit()
        await db.refresh(user)

        status_str = "activated" if is_active else "deactivated"
        app_logger.info(
            f"Admin {admin_user.email} {status_str} user {user.email}"
        )
        return user

    async def get_user_stats(self, db: AsyncSession) -> dict:
        """Counts by role and verification status."""
        total = (await db.execute(select(func.count(User.id)))).scalar() or 0
        by_role = {}
        for role_name in ("user", "vendor", "superadmin"):
            count = (
                await db.execute(
                    select(func.count(User.id)).filter(User.role == role_name)
                )
            ).scalar() or 0
            by_role[role_name] = count

        active = (
            await db.execute(
                select(func.count(User.id)).filter(User.is_active == True)
            )
        ).scalar() or 0
        inactive = total - active

        return {
            "total": total,
            "by_role": by_role,
            "active": active,
            "inactive": inactive,
        }

    # -------------------------------------------------------------------
    # Property Management
    # -------------------------------------------------------------------

    async def list_properties(
        self,
        db: AsyncSession,
        status_filter: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        """List all properties with optional filters."""
        query = select(Property)

        if status_filter:
            query = query.filter(Property.status == status_filter)

        if search:
            search_term = f"%{search.lower()}%"
            query = query.filter(
                (Property.name.ilike(search_term))
                | (Property.location.ilike(search_term))
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar() or 0

        offset = (page - 1) * limit
        query = query.order_by(Property.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        properties = result.scalars().all()

        # Attach owner info
        enriched = []
        for prop in properties:
            owner = await self._get_user_safe(prop.user_id, db)
            prop_dict = {
                "id": prop.id,
                "user_id": prop.user_id,
                "name": prop.name,
                "type": prop.type,
                "location": prop.location,
                "description": prop.description,
                "beds": prop.beds,
                "baths": prop.baths,
                "guests": prop.guests,
                "price": prop.price,
                "photos": prop.photos,
                "video_url": prop.video_url,
                "amenities": prop.amenities,
                "payout_account": prop.payout_account,
                "payout_bank": prop.payout_bank,
                "payout_name": prop.payout_name,
                "status": prop.status,
                "admin_notes": getattr(prop, "admin_notes", None),
                "created_at": prop.created_at,
                "updated_at": prop.updated_at,
                "owner_name": f"{owner.first_name} {owner.last_name}" if owner else None,
                "owner_email": owner.email if owner else None,
            }
            enriched.append(prop_dict)

        return {"total": total, "page": page, "limit": limit, "properties": enriched}

    async def get_property_detail(self, property_id: str, db: AsyncSession) -> dict:
        """Get a single property with owner details."""
        result = await db.execute(
            select(Property).filter(Property.id == property_id)
        )
        prop = result.scalars().first()
        if not prop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Property not found."
            )
        owner = await self._get_user_safe(prop.user_id, db)
        return {
            "id": prop.id,
            "user_id": prop.user_id,
            "name": prop.name,
            "type": prop.type,
            "location": prop.location,
            "description": prop.description,
            "beds": prop.beds,
            "baths": prop.baths,
            "guests": prop.guests,
            "price": prop.price,
            "photos": prop.photos,
            "video_url": prop.video_url,
            "amenities": prop.amenities,
            "payout_account": prop.payout_account,
            "payout_bank": prop.payout_bank,
            "payout_name": prop.payout_name,
            "status": prop.status,
            "admin_notes": getattr(prop, "admin_notes", None),
            "created_at": prop.created_at,
            "updated_at": prop.updated_at,
            "owner_name": f"{owner.first_name} {owner.last_name}" if owner else None,
            "owner_email": owner.email if owner else None,
        }

    async def change_property_status(
        self,
        property_id: str,
        new_status: str,
        admin_notes: Optional[str],
        admin_user: User,
        db: AsyncSession,
    ) -> Property:
        """Approve / reject / suspend a property listing."""
        result = await db.execute(
            select(Property).filter(Property.id == property_id)
        )
        prop = result.scalars().first()
        if not prop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Property not found."
            )

        old_status = prop.status
        prop.status = new_status
        if admin_notes is not None and hasattr(prop, "admin_notes"):
            prop.admin_notes = admin_notes

        await db.commit()
        await db.refresh(prop)

        app_logger.info(
            f"Admin {admin_user.email} changed property {prop.id} status: {old_status} -> {new_status}"
        )
        return prop

    # -------------------------------------------------------------------
    # Ride Management
    # -------------------------------------------------------------------

    async def list_rides(
        self,
        db: AsyncSession,
        status_filter: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        """List all rides with optional filters."""
        query = select(Ride).options(selectinload(Ride.media))

        if status_filter:
            query = query.filter(Ride.status == status_filter)

        if search:
            search_term = f"%{search.lower()}%"
            query = query.filter(Ride.pickup_location.ilike(search_term))

        count_base = select(Ride)
        if status_filter:
            count_base = count_base.filter(Ride.status == status_filter)
        if search:
            count_base = count_base.filter(Ride.pickup_location.ilike(f"%{search.lower()}%"))
        count_query = select(func.count()).select_from(count_base.subquery())
        total = (await db.execute(count_query)).scalar() or 0

        offset = (page - 1) * limit
        query = query.order_by(Ride.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        rides = result.scalars().unique().all()

        enriched = []
        for ride in rides:
            owner = await self._get_user_safe(ride.user_id, db)
            ride_dict = {
                "id": ride.id,
                "user_id": ride.user_id,
                "ride_type": ride.ride_type.value if hasattr(ride.ride_type, 'value') else str(ride.ride_type),
                "seat_count": ride.seat_count,
                "door_count": ride.door_count,
                "pickup_location": ride.pickup_location,
                "pickup_latitude": ride.pickup_latitude,
                "pickup_longitude": ride.pickup_longitude,
                "adult_passenger_count": ride.adult_passenger_count,
                "children_passenger_count": ride.children_passenger_count,
                "infant_passenger_count": ride.infant_passenger_count,
                "features": ride.features,
                "price": ride.price,
                "currency": ride.currency,
                "status": ride.status.value if hasattr(ride.status, 'value') else str(ride.status),
                "admin_notes": getattr(ride, "admin_notes", None),
                "created_at": ride.created_at,
                "updated_at": ride.updated_at,
                "owner_name": f"{owner.first_name} {owner.last_name}" if owner else None,
                "owner_email": owner.email if owner else None,
            }
            enriched.append(ride_dict)

        return {"total": total, "page": page, "limit": limit, "rides": enriched}

    async def get_ride_detail(self, ride_id: str, db: AsyncSession) -> dict:
        """Get a single ride with owner details."""
        result = await db.execute(
            select(Ride).options(selectinload(Ride.media)).filter(Ride.id == ride_id)
        )
        ride = result.scalars().first()
        if not ride:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found."
            )
        owner = await self._get_user_safe(ride.user_id, db)
        return {
            "id": ride.id,
            "user_id": ride.user_id,
            "ride_type": ride.ride_type.value if hasattr(ride.ride_type, 'value') else str(ride.ride_type),
            "seat_count": ride.seat_count,
            "door_count": ride.door_count,
            "pickup_location": ride.pickup_location,
            "pickup_latitude": ride.pickup_latitude,
            "pickup_longitude": ride.pickup_longitude,
            "adult_passenger_count": ride.adult_passenger_count,
            "children_passenger_count": ride.children_passenger_count,
            "infant_passenger_count": ride.infant_passenger_count,
            "features": ride.features,
            "price": ride.price,
            "currency": ride.currency,
            "status": ride.status.value if hasattr(ride.status, 'value') else str(ride.status),
            "admin_notes": getattr(ride, "admin_notes", None),
            "created_at": ride.created_at,
            "updated_at": ride.updated_at,
            "owner_name": f"{owner.first_name} {owner.last_name}" if owner else None,
            "owner_email": owner.email if owner else None,
        }

    async def change_ride_status(
        self,
        ride_id: str,
        new_status: str,
        admin_notes: Optional[str],
        admin_user: User,
        db: AsyncSession,
    ) -> Ride:
        """Approve / reject / suspend a ride listing."""
        result = await db.execute(select(Ride).filter(Ride.id == ride_id))
        ride = result.scalars().first()
        if not ride:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found."
            )

        old_status = ride.status
        # Try to convert to enum, fallback to string
        try:
            ride.status = RideStatus(new_status)
        except ValueError:
            ride.status = new_status

        if admin_notes is not None and hasattr(ride, "admin_notes"):
            ride.admin_notes = admin_notes

        await db.commit()
        await db.refresh(ride)

        app_logger.info(
            f"Admin {admin_user.email} changed ride {ride.id} status: {old_status} -> {new_status}"
        )
        return ride

    # -------------------------------------------------------------------
    # Support Ticket Management
    # -------------------------------------------------------------------

    async def list_tickets(
        self,
        db: AsyncSession,
        status_filter: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        """List all support tickets with optional status filter."""
        query = select(SupportTicket)

        if status_filter:
            query = query.filter(SupportTicket.status == status_filter)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar() or 0

        offset = (page - 1) * limit
        query = query.order_by(SupportTicket.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        tickets = result.scalars().all()

        # Enrich with user info
        enriched = []
        for ticket in tickets:
            owner = await self._get_user_safe(ticket.user_id, db)
            enriched.append({
                "id": ticket.id,
                "user_id": ticket.user_id,
                "subject": ticket.subject,
                "category": ticket.category,
                "message": ticket.message,
                "status": ticket.status,
                "created_at": ticket.created_at,
                "updated_at": ticket.updated_at,
                "user_name": f"{owner.first_name} {owner.last_name}" if owner else None,
                "user_email": owner.email if owner else None,
            })

        return {"total": total, "page": page, "limit": limit, "tickets": enriched}

    async def change_ticket_status(
        self,
        ticket_id: str,
        new_status: str,
        admin_user: User,
        db: AsyncSession,
    ) -> SupportTicket:
        """Update a support ticket's status."""
        result = await db.execute(
            select(SupportTicket).filter(SupportTicket.id == ticket_id)
        )
        ticket = result.scalars().first()
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Support ticket not found.",
            )

        old_status = ticket.status
        ticket.status = new_status
        await db.commit()
        await db.refresh(ticket)

        app_logger.info(
            f"Admin {admin_user.email} changed ticket {ticket.id} status: {old_status} -> {new_status}"
        )
        return ticket

    # -------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------

    async def _get_user_safe(self, user_id: str, db: AsyncSession) -> Optional[User]:
        """Get user by ID, returning None if not found."""
        result = await db.execute(select(User).filter(User.id == user_id))
        return result.scalars().first()


# Singleton
admin_service = AdminService()
