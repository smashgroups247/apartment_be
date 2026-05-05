"""Favorite Model"""
from sqlalchemy import Column, String, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from api.v1.models.base_model import BaseTableModel


class Favorite(BaseTableModel):
    __tablename__ = "favorites"

    user_id       = Column(String, ForeignKey("users.id"), nullable=False)
    item_id       = Column(String, nullable=False)
    item_type     = Column(String(50), nullable=False)   # "stay" | "car_rental"
    item_name     = Column(String(255), nullable=False)
    item_location = Column(String(255), nullable=False)
    item_image    = Column(String, nullable=True)
    item_rating   = Column(Numeric(3, 1), nullable=True)
    item_price    = Column(Numeric(10, 2), nullable=False)

    user = relationship("User", backref="favorites")

    __table_args__ = (
        UniqueConstraint("user_id", "item_type", "item_id", name="uq_user_item_favorite"),
    )

    def __repr__(self):
        return f"<Favorite id={self.id} user={self.user_id} type={self.item_type} item={self.item_id}>"