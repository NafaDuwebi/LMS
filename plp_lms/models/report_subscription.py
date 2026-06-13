from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Time, JSON
from sqlalchemy.sql import func
from database import Base


class ReportSubscription(Base):
    __tablename__ = "report_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    recipient_emails = Column(JSON, nullable=True)
    frequency = Column(String(20), nullable=False)
    day_of_week = Column(Integer, nullable=True)
    day_of_month = Column(Integer, nullable=True)
    send_time = Column(Time, nullable=True)
    last_sent_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
