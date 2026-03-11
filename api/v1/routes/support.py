"""
Support Router
File: api/v1/routes/support.py

Endpoints:
  POST /support/ticket          – submit a new support ticket
  GET  /support/tickets         – list own tickets (admin: all tickets)
  GET  /support/ticket/{id}     – get a single ticket by ID
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.database import get_db
from api.utils.jwt_handler import get_current_user
from api.utils.success_response import success_response
from api.v1.models.users import User
from api.v1.schemas.support import CreateTicketRequest, TicketResponse, TicketListResponse
from api.v1.services.support import support_service


support = APIRouter(prefix="/support", tags=["Support"])


# ---------------------------------------------------------------------------
# POST /support/ticket — Submit a new ticket
# ---------------------------------------------------------------------------

@support.post(
    "/ticket",
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new support ticket",
    response_model=None,
)
async def create_ticket(
    schema: CreateTicketRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new support ticket for the authenticated user.
    Status is set to 'open' automatically.
    """
    ticket = await support_service.create_ticket(
        schema=schema, user=current_user, db=db
    )
    return success_response(
        status_code=status.HTTP_201_CREATED,
        message="Your support ticket has been submitted. We'll get back to you shortly.",
        data=TicketResponse.model_validate(ticket).model_dump(),
    )


# ---------------------------------------------------------------------------
# GET /support/tickets — List tickets
# ---------------------------------------------------------------------------

@support.get(
    "/tickets",
    status_code=status.HTTP_200_OK,
    summary="List support tickets (own for user, all for admin)",
    response_model=None,
)
async def get_tickets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns all support tickets belonging to the current user.
    Admin users receive all tickets across the platform.
    """
    tickets = await support_service.get_tickets(user=current_user, db=db)
    ticket_data = [TicketResponse.model_validate(t).model_dump() for t in tickets]
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Tickets retrieved successfully.",
        data={"total": len(ticket_data), "tickets": ticket_data},
    )


# ---------------------------------------------------------------------------
# GET /support/ticket/{id} — Get single ticket
# ---------------------------------------------------------------------------

@support.get(
    "/ticket/{ticket_id}",
    status_code=status.HTTP_200_OK,
    summary="Get a single support ticket by ID",
    response_model=None,
)
async def get_ticket(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns a single ticket. Returns 403 if the ticket belongs to a different user.
    Admin users can access any ticket.
    """
    ticket = await support_service.get_ticket(
        ticket_id=ticket_id, user=current_user, db=db
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Ticket retrieved successfully.",
        data=TicketResponse.model_validate(ticket).model_dump(),
    )