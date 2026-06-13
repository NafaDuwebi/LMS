from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Date, Float, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Cohort(Base):
    __tablename__ = "cohorts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    trainer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    max_learners = Column(Integer, default=30)
    enrolment_token = Column(String(100), unique=True, nullable=True)
    is_active = Column(Boolean, default=True)
    delivery_mode = Column(String(50), default="online")
    venue = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    course = relationship("Course", back_populates="cohorts")
    trainer = relationship("User", foreign_keys=[trainer_id])
    enrolments = relationship("Enrolment", back_populates="cohort", cascade="all, delete-orphan")
    attendance_records = relationship("AttendanceRecord", back_populates="cohort", cascade="all, delete-orphan")


class Enrolment(Base):
    __tablename__ = "enrolments"
    __table_args__ = (Index("ix_enrolments_user_cohort_status", "user_id", "cohort_id", "status"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    cohort_id = Column(Integer, ForeignKey("cohorts.id"), nullable=False)
    enrolled_at = Column(DateTime, server_default=func.now())
    completion_date = Column(DateTime, nullable=True)
    status = Column(String(20), default="enrolled")
    final_score = Column(Float, nullable=True)
    enrolment_source = Column(String(20), default="self")
    waitlisted = Column(Boolean, default=False)
    retention_review_date = Column(Date, nullable=True)
    retention_status = Column(String(20), default="active")

    cohort = relationship("Cohort", back_populates="enrolments")
    user = relationship("User", foreign_keys=[user_id])
    attendance_records = relationship("AttendanceRecord", back_populates="enrolment", foreign_keys="[AttendanceRecord.enrolment_id]")


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, index=True)
    enrolment_id = Column(Integer, ForeignKey("enrolments.id"), nullable=False)
    cohort_id = Column(Integer, ForeignKey("cohorts.id"), nullable=False)
    session_date = Column(Date, nullable=False)
    attended = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    recorded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    enrolment = relationship("Enrolment", back_populates="attendance_records", foreign_keys=[enrolment_id])
    cohort = relationship("Cohort", back_populates="attendance_records", foreign_keys=[cohort_id])
    recorder = relationship("User", foreign_keys=[recorded_by])
