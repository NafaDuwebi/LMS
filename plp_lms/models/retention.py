from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from database import Base


class RetentionLog(Base):
    __tablename__ = "retention_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(30), nullable=False)
    actioned_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    actioned_at = Column(DateTime, server_default=func.now())
    notes = Column(Text, nullable=True)
