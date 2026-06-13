from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    course_code = Column(String(20), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    awarding_body = Column(String(100), nullable=True)
    level = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    pass_mark = Column(Float, default=55.0)
    duration_hours = Column(Integer, nullable=True)
    assessment_type = Column(String(50), nullable=True)
    delivery_mode = Column(String(50), nullable=True)
    cert_validity_years = Column(Integer, default=0)
    is_published = Column(Boolean, default=True)
    prerequisites = Column(JSON, nullable=True)
    credit_value = Column(Integer, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    modules = relationship("Module", back_populates="course", cascade="all, delete-orphan", order_by="Module.order_index")
    learning_outcomes = relationship("LearningOutcome", back_populates="course", cascade="all, delete-orphan", order_by="LearningOutcome.order_index")
    cohorts = relationship("Cohort", back_populates="course", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="course", cascade="all, delete-orphan")
    certificates = relationship("Certificate", back_populates="course", cascade="all, delete-orphan")


class LearningOutcome(Base):
    __tablename__ = "learning_outcomes"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    outcome_text = Column(Text, nullable=False)
    syllabus_area = Column(String(100), nullable=True)
    order_index = Column(Integer, default=0)

    course = relationship("Course", back_populates="learning_outcomes")


class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, default=0)
    is_published = Column(Boolean, default=True)
    delivery_mode = Column(String(50), default="online")
    created_at = Column(DateTime, server_default=func.now())

    course = relationship("Course", back_populates="modules")
    materials = relationship("Material", back_populates="module", cascade="all, delete-orphan")


class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False)
    title = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)
    file_path = Column(String(500), nullable=True)
    file_size_kb = Column(Integer, nullable=True)
    url = Column(String(500), nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    uploaded_at = Column(DateTime, server_default=func.now())

    module = relationship("Module", back_populates="materials")
