"""Car Rental Booking Model"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Text, Time
from sqlalchemy.orm import relationship
from api.v1.models.base_model import BaseTableModel


class CarRental(BaseTableModel):
    __tablename__ = "car_rentals"

    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Car details stored directly
    car_name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    car_image = Column(Text, nullable=True)
    car_rating = Column(Numeric(3, 1), nullable=True)

    # Booking details
    pick_up_date = Column(DateTime(timezone=True), nullable=False)
    pick_up_time = Column(String(20), nullable=False)
    return_date = Column(DateTime(timezone=True), nullable=False)
    return_time = Column(String(20), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    status = Column(String(50), default="pending", nullable=False)

    user = relationship("User", backref="car_rentals")

    def __repr__(self):
        return f"<CarRental id={self.id} user={self.user_id} status={self.status}>"