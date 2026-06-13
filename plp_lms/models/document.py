from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class EnrolmentDocumentRequirement(Base):
    __tablename__ = "enrolment_document_requirements"

    id = Column(Integer, primary_key=True, index=True)
    cohort_id = Column(Integer, ForeignKey("cohorts.id"), nullable=False)
    document_label = Column(String(255), nullable=False)
    instructions = Column(Text, nullable=True)
    is_required = Column(Boolean, default=True)

    cohort = relationship("Cohort")
    submissions = relationship("EnrolmentDocumentSubmission", back_populates="requirement", cascade="all, delete-orphan")


class EnrolmentDocumentSubmission(Base):
    __tablename__ = "enrolment_document_submissions"

    id = Column(Integer, primary_key=True, index=True)
    requirement_id = Column(Integer, ForeignKey("enrolment_document_requirements.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_path = Column(String(500), nullable=True)
    uploaded_at = Column(DateTime, server_default=func.now())
    status = Column(String(20), default="pending")
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    requirement = relationship("EnrolmentDocumentRequirement", back_populates="submissions")
    user = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
