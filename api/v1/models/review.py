"""Review Model"""

from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from api.v1.models.base_model import BaseTableModel


class Review(BaseTableModel):
    __tablename__ = "reviews"

    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    booking_id = Column(String, nullable=False)
    booking_type = Column(String(20), nullable=False, default="stay")  # "stay" or "car_rental"
    review_text = Column(Text, nullable=False)
    rating = Column(Integer, nullable=False)
    item_image = Column(String, nullable=True)
    item_name = Column(String(255), nullable=True)

    user = relationship("User", backref="reviews")

    def __repr__(self):
        return f"<Review id={self.id} booking={self.booking_id} type={self.booking_type}>"