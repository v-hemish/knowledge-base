from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from db.db import Base


class Potion(Base):
    __tablename__ = "potions"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    stock = Column(Integer)
    price = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
