"""
Support Ticket Model
File: api/v1/models/support_ticket.py
"""

from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from api.v1.models.base_model import BaseTableModel


class SupportTicket(BaseTableModel):
    __tablename__ = "support_tickets"

    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subject = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="open")
    # status values: "open" | "in_progress" | "resolved"

    user = relationship("User", backref="support_tickets")

    def __repr__(self) -> str:
        return f"<SupportTicket id={self.id} user_id={self.user_id} status={self.status}>"