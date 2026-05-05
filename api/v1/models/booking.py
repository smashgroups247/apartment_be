"""Booking Model"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Integer, Text
from sqlalchemy.orm import relationship
from api.v1.models.base_model import BaseTableModel


class Booking(BaseTableModel):
    __tablename__ = "bookings"

    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Apartment details stored directly
    apartment_name = Column(String(255), nullable=False)
    apartment_location = Column(String(255), nullable=False)
    apartment_image = Column(Text, nullable=True)
    apartment_rating = Column(Numeric(3, 1), nullable=True)
    
    # Booking details
    check_in = Column(DateTime(timezone=True), nullable=False)
    check_out = Column(DateTime(timezone=True), nullable=False)
    guests = Column(Integer, nullable=False, default=1)
    total_price = Column(Numeric(10, 2), nullable=False)
    status = Column(String(50), default="pending", nullable=False)

    user = relationship("User", backref="bookings")

    def __repr__(self):
        return f"<Booking id={self.id} user={self.user_id} status={self.status}>"