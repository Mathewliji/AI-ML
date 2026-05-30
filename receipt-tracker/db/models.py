import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from db.database import Base


class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)
    merchant = Column(String(255), nullable=False)
    date = Column(String(20), default="")
    subtotal = Column(Float, default=0.0)
    tax = Column(Float, default=0.0)
    total = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    category = Column(String(50), default="other")
    raw_text = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    items = relationship("LineItem", back_populates="receipt", cascade="all, delete-orphan")


class LineItem(Base):
    __tablename__ = "line_items"

    id = Column(Integer, primary_key=True, index=True)
    receipt_id = Column(Integer, ForeignKey("receipts.id"), nullable=False)
    description = Column(String(255), default="")
    quantity = Column(Float, default=1.0)
    unit_price = Column(Float, default=0.0)
    total = Column(Float, nullable=False)

    receipt = relationship("Receipt", back_populates="items")
