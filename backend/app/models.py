from sqlalchemy import Boolean, Column, Float, Integer, String

from .database import Base


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(String(500), nullable=True)
    price = Column(Float, nullable=False, default=0.0)
    in_stock = Column(Boolean, nullable=False, default=True)
