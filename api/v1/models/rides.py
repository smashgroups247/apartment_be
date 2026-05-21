"""
Rides Models
File: api/v1/models/rides.py
"""

from sqlalchemy import Column, String, Text, ForeignKey, Integer, Float, Index, JSON, Enum
from sqlalchemy.orm import relationship
import enum
from api.v1.models.base_model import BaseTableModel

class RideType(str, enum.Enum):
    sedan = "sedan"
    suv = "suv"
    van = "van"

class RideStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    inactive = "inactive"
    pending_approval = "pending_approval"
    rejected = "rejected"
    suspended = "suspended"

class RideMedia(BaseTableModel):
    __tablename__ = "ride_media"

    ride_id = Column(String(36), ForeignKey("rides.id", ondelete="CASCADE"), nullable=False, index=True)
    media_type = Column(String(50), nullable=False) # 'image' or 'video'
    url = Column(String(255), nullable=False)
    public_id = Column(String(255), nullable=True)
    resource_type = Column(String(50), nullable=True) # Cloudinary resource type
    format = Column(String(50), nullable=True) # File format (jpg, mp4, etc.)
    position = Column(Integer, default=0)

    ride = relationship("Ride", back_populates="media")

class Ride(BaseTableModel):
    __tablename__ = "rides"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Ride Description
    ride_type = Column(Enum(RideType), nullable=False)
    seat_count = Column(Integer, nullable=False)
    door_count = Column(Integer, nullable=False)

    # Pickup & Capacity
    pickup_location = Column(String(255), nullable=False)
    pickup_latitude = Column(Float, nullable=True)
    pickup_longitude = Column(Float, nullable=True)
    adult_passenger_count = Column(Integer, nullable=False, default=0)
    children_passenger_count = Column(Integer, nullable=False, default=0)
    infant_passenger_count = Column(Integer, nullable=False, default=0)

    # Features
    features = Column(JSON, default=list) # List of feature names

    # Pricing
    price = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False, default="NGN")
    
    # Status
    status = Column(Enum(RideStatus), default=RideStatus.published)

    # Admin notes (rejection reason, etc.)
    admin_notes = Column(Text, nullable=True)

    # Relationships
    media = relationship("RideMedia", back_populates="ride", cascade="all, delete-orphan", lazy="selectin")

    @property
    def photos(self):
        return [m for m in self.media if m.media_type == "image"]

    @property
    def video(self):
        videos = [m for m in self.media if m.media_type == "video"]
        return videos[0] if videos else None

    __table_args__ = (
        # Unique constraint to help prevent duplicates
        Index(
            "ix_rides_unique_listing",
            "user_id", "ride_type", "seat_count", "door_count", "pickup_location",
            unique=True
        ),
    )

    def __repr__(self) -> str:
        return f"<Ride id={self.id} type={self.ride_type}>"
