"""User Model - api/v1/models/users.py"""

from sqlalchemy import Boolean, Column, String, DateTime, Text
from api.v1.models.base_model import BaseTableModel


class User(BaseTableModel):
    __tablename__ = "users"

    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    username = Column(String(100), unique=True, nullable=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    role = Column(String(50), default="user", nullable=False)

    # NEW: account management fields
    phone_number = Column(String(20), nullable=True)
    avatar_url = Column(Text, nullable=True)

    hashed_refresh_token = Column(Text, nullable=True)
    hashed_reset_token = Column(Text, nullable=True)
    reset_token_expires_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"