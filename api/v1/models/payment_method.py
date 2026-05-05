"""Payment Method Model"""

from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from api.v1.models.base_model import BaseTableModel


class PaymentMethod(BaseTableModel):
    __tablename__ = "payment_methods"

    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    card_number = Column(String(255), nullable=False)  # store masked e.g. 1352 **** **** ****
    last_four = Column(String(4), nullable=False)
    card_type = Column(String(20), nullable=False)  # mastercard, visa, verve
    expiration = Column(String(10), nullable=False)  # MM/YY
    cvv = Column(String(255), nullable=False)  # hashed
    country = Column(String(100), nullable=False, default="Nigeria")
    is_default = Column(Boolean, default=False, nullable=False)

    user = relationship("User", backref="payment_methods")

    def __repr__(self):
        return f"<PaymentMethod id={self.id} type={self.card_type} last4={self.last_four}>"