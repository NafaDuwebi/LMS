from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class RplClaim(Base):
    __tablename__ = "rpl_claims"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    prior_title = Column(String(255), nullable=False)
    prior_provider = Column(String(255), nullable=True)
    completion_date = Column(Date, nullable=True)
    evidence_path = Column(String(500), nullable=True)
    statement = Column(Text, nullable=True)
    status = Column(String(20), default="pending")
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    submitted_at = Column(DateTime, server_default=func.now())

    user = relationship("User", foreign_keys=[user_id])
    course = relationship("Course")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
