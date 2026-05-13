"""Apartment Model"""

from sqlalchemy import Column, String, Integer, Numeric, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from api.v1.models.base_model import BaseTableModel


class Apartment(BaseTableModel):
    __tablename__ = "apartments"

    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Basic Info
    name = Column(String(255), nullable=True)
    type = Column(String(100), nullable=False)  # Studio, Duplex, etc.
    location = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    beds = Column(Integer, default=1)
    baths = Column(Integer, default=1)
    
    # Guests info
    adults = Column(Integer, default=0)
    children = Column(Integer, default=0)
    infants = Column(Integer, default=0)

    # Media
    images = Column(JSON, nullable=True)  # List of URLs
    video = Column(String(255), nullable=True)

    # Features/Amenities
    features = Column(JSON, nullable=True)  # Dict of amenities

    # Pricing
    price = Column(Numeric(10, 2), nullable=False)

    # Payout Info
    account_number = Column(String(50), nullable=True)
    bank = Column(String(100), nullable=True)
    account_name = Column(String(255), nullable=True)

    status = Column(String(50), default="active", nullable=False)

    user = relationship("User", backref="apartments")

    def __repr__(self):
        return f"<Apartment id={self.id} name={self.name} user={self.user_id}>"
