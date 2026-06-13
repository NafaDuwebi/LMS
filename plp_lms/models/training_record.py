from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class TrainingRecord(Base):
    __tablename__ = "training_record"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    record_type = Column(String(30), nullable=False)
    title = Column(String(255), nullable=False)
    provider = Column(String(255), nullable=True)
    completion_date = Column(DateTime, nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    hours = Column(Float, nullable=True)
    evidence_path = Column(String(500), nullable=True)
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)

    user = relationship("User", foreign_keys=[user_id])
    verifier = relationship("User", foreign_keys=[verified_by])
