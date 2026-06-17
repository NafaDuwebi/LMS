from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class EnrolmentRequest(Base):
    __tablename__ = "enrolment_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    message = Column(Text, nullable=True)
    status = Column(String(20), default="pending")
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    cohort_id = Column(Integer, ForeignKey("cohorts.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", foreign_keys=[user_id])
    course = relationship("Course", foreign_keys=[course_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    cohort = relationship("Cohort", foreign_keys=[cohort_id])
