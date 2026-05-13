"""
Property Model
File: api/v1/models/property.py
"""

from sqlalchemy import Column, String, Text, Float, Integer, JSON, UniqueConstraint, ForeignKey
from sqlalchemy.orm import relationship
from api.v1.models.base_model import BaseTableModel


class Property(BaseTableModel):
    __tablename__ = "properties"

    __table_args__ = (
        UniqueConstraint("user_id", "name", "location", name="uq_property_user_name_location"),
    )

    # Ownership
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Basic info
    name        = Column(String(255), nullable=False)
    type        = Column(String(100), nullable=False)
    location    = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)

    # Capacity
    beds   = Column(Integer, nullable=False, default=1)
    baths  = Column(Integer, nullable=False, default=1)
    guests = Column(JSON, nullable=True)

    # Pricing
    price = Column(Float, nullable=False, default=0.0)

    # Media — Cloudinary URLs
    photos    = Column(JSON, nullable=True, default=list)
    video_url = Column(String(1000), nullable=True)

    # Amenities
    amenities = Column(JSON, nullable=True, default=list)

    # Payout
    payout_account = Column(String(20), nullable=True)
    payout_bank    = Column(String(100), nullable=True)
    payout_name    = Column(String(255), nullable=True)

    # Status
    status = Column(String(50), nullable=False, default="active")

    user = relationship("User", backref="properties")

    def __repr__(self):
        return f"<Property id={self.id} name={self.name!r} status={self.status}>"