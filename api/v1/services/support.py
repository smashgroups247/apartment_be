"""
Support Ticket Service
File: api/v1/services/support.py
"""

from typing import List

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from api.loggers.app_logger import app_logger
from api.v1.models.support_ticket import SupportTicket
from api.v1.models.users import User
from api.v1.schemas.support import CreateTicketRequest


class SupportService:
    """Business logic for support ticket operations."""

    # -----------------------------------------------------------------------
    # Create Ticket
    # -----------------------------------------------------------------------

    async def create_ticket(
        self, schema: CreateTicketRequest, user: User, db: AsyncSession
    ) -> SupportTicket:
        """
        Create a new support ticket for the authenticated user.
        Sets status to 'open' by default.
        Triggers an email notification (stubbed — wire up when email service is ready).
        """
        ticket = SupportTicket(
            user_id=user.id,
            subject=schema.subject,
            category=schema.category,
            message=schema.message,
            status="open",
        )
        db.add(ticket)
        await db.commit()
        await db.refresh(ticket)

        app_logger.info(
            f"Support ticket created: id={ticket.id} user_id={user.id} category={ticket.category}"
        )

        # TODO: Send email notification to support team when email service is configured
        # await send_support_email(
        #     to="complaints@smashapartments.com",
        #     subject=f"New Support Ticket [{ticket.category}]: {ticket.subject}",
        #     body=f"From: {user.email}\n\n{ticket.message}",
        # )

        return ticket

    # -----------------------------------------------------------------------
    # Get All Tickets (own for user, all for admin)
    # -----------------------------------------------------------------------

    async def get_tickets(
        self, user: User, db: AsyncSession
    ) -> List[SupportTicket]:
        """
        Return tickets for the current user.
        If the user has role 'admin', return all tickets across all users.
        Results are ordered newest first.
        """
        if user.role == "admin":
            result = await db.execute(
                select(SupportTicket).order_by(desc(SupportTicket.created_at))
            )
        else:
            result = await db.execute(
                select(SupportTicket)
                .filter(SupportTicket.user_id == user.id)
                .order_by(desc(SupportTicket.created_at))
            )

        return result.scalars().all()

    # -----------------------------------------------------------------------
    # Get Single Ticket
    # -----------------------------------------------------------------------

    async def get_ticket(
        self, ticket_id: str, user: User, db: AsyncSession
    ) -> SupportTicket:
        """
        Return a single ticket by ID.
        Raises 404 if not found.
        Raises 403 if the ticket belongs to another user (unless admin).
        """
        result = await db.execute(
            select(SupportTicket).filter(SupportTicket.id == ticket_id)
        )
        ticket = result.scalars().first()

        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Support ticket not found.",
            )

        if user.role != "admin" and ticket.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this ticket.",
            )

        return ticket


support_service = SupportService()