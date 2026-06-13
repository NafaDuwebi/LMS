from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (Index("ix_submissions_user_assessment", "user_id", "assessment_id"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    attempt_number = Column(Integer, default=1)
    submitted_at = Column(DateTime, server_default=func.now())
    score = Column(Float, nullable=True)
    passed = Column(Boolean, nullable=True)
    status = Column(String(20), default="submitted")
    feedback = Column(Text, nullable=True)
    malpractice_flag = Column(Boolean, default=False)
    malpractice_notes = Column(Text, nullable=True)
    marked_at = Column(DateTime, nullable=True)
    marked_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    user = relationship("User", foreign_keys=[user_id])
    assessment = relationship("Assessment", back_populates="submissions")
    answers = relationship("Answer", back_populates="submission", cascade="all, delete-orphan")


class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    answer_text = Column(Text, nullable=True)
    selected_option_id = Column(Integer, nullable=True)
    marks_awarded = Column(Float, nullable=True)
    marker_feedback = Column(Text, nullable=True)

    submission = relationship("Submission", back_populates="answers")
    question = relationship("Question", back_populates="answers")
