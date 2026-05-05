"""Payment Model"""

from sqlalchemy import Column, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from api.v1.models.base_model import BaseTableModel


class Payment(BaseTableModel):
    __tablename__ = "payments"

    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    reference = Column(String(255), unique=True, nullable=False)
    purpose = Column(String(50), nullable=False)  # "apartment" or "car_rental"
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # pending, success, failed
    mode = Column(String(50), nullable=True)  # Paystack, Card, Transfer
    booking_id = Column(String, nullable=True)
    car_rental_id = Column(String, nullable=True)

    user = relationship("User", backref="payments")

    def __repr__(self):
        return f"<Payment id={self.id} ref={self.reference} status={self.status}>"