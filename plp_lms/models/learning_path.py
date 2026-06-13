from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class LearningPath(Base):
    __tablename__ = "learning_paths"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_published = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    courses = relationship("LearningPathCourse", back_populates="path", cascade="all, delete-orphan")
    enrolments = relationship("LearningPathEnrolment", back_populates="path", cascade="all, delete-orphan")


class LearningPathCourse(Base):
    __tablename__ = "learning_path_courses"

    id = Column(Integer, primary_key=True, index=True)
    path_id = Column(Integer, ForeignKey("learning_paths.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    order_index = Column(Integer, default=0)
    unlock_on_previous = Column(Boolean, default=True)

    path = relationship("LearningPath", back_populates="courses")
    course = relationship("Course")


class LearningPathEnrolment(Base):
    __tablename__ = "learning_path_enrolments"
    __table_args__ = (Index("ix_learning_path_enrolments_user_path", "user_id", "path_id"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    path_id = Column(Integer, ForeignKey("learning_paths.id"), nullable=False)
    enrolled_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="enrolled")

    path = relationship("LearningPath", back_populates="enrolments")
    user = relationship("User", foreign_keys=[user_id])
