"""
Models package – import all models here so Alembic autogenerate can detect them.
"""

from api.v1.models.base_model import BaseTableModel
from api.v1.models.users import User
from api.v1.models.support_ticket import SupportTicket


__all__ = [
    "BaseTableModel",
    "User",
    "SupportTicket"
]

