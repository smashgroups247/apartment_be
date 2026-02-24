"""This is the Base Model Class"""

from uuid_extensions import uuid7
from fastapi import Depends
from api.db.database import Base
from sqlalchemy import Column, String, DateTime, func


class BaseTableModel(Base):
    """This model creates helper methods for all models"""

    __abstract__ = True

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid7().hex))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def to_dict(self):
        """returns a dictionary representation of the instance"""
        obj_dict = self.__dict__.copy()
        del obj_dict["_sa_instance_state"]
        obj_dict["id"] = self.id
        if self.created_at:
            obj_dict["created_at"] = self.created_at.isoformat()
        if self.updated_at:
            obj_dict["updated_at"] = self.updated_at.isoformat()
        return obj_dict

    @classmethod
    async def get_all(cls, db):
        from sqlalchemy.future import select
        """ returns all instance of the class in the db """
        result = await db.execute(select(cls))
        return result.scalars().all()

    @classmethod
    async def get_by_id(cls, db, id):
        from sqlalchemy.future import select
        """ returns a single object from the db """
        result = await db.execute(select(cls).filter_by(id=id))
        return result.scalars().first()
