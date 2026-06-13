from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.sql import func
from database import Base


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (Index("ix_messages_user_read", "user_id", "is_read"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject = Column(String(255), nullable=False)
    body_html = Column(Text, nullable=True)
    triggered_by = Column(String(50), nullable=True)
    sent_at = Column(DateTime, server_default=func.now())
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
