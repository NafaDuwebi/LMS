from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=True)
    title = Column(String(255), nullable=False)
    type = Column(String(20), nullable=False)
    max_attempts = Column(Integer, default=1)
    pass_mark = Column(Float, nullable=True)
    time_limit_mins = Column(Integer, nullable=True)
    is_published = Column(Boolean, default=True)
    randomise_questions = Column(Boolean, default=False)
    randomise_options = Column(Boolean, default=False)
    release_results_immediately = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    course = relationship("Course", back_populates="assessments")
    module = relationship("Module", backref="assessments")
    questions = relationship("Question", back_populates="assessment", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="assessment", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(20), nullable=False)
    marks = Column(Float, default=1.0)
    order_index = Column(Integer, default=0)
    syllabus_area_tag = Column(String(100), nullable=True)

    assessment = relationship("Assessment", back_populates="questions")
    answer_options = relationship("AnswerOption", back_populates="question", cascade="all, delete-orphan")
    answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan")


class AnswerOption(Base):
    __tablename__ = "answer_options"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    option_text = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False)

    question = relationship("Question", back_populates="answer_options")


class QuestionBank(Base):
    __tablename__ = "question_bank"

    id = Column(Integer, primary_key=True, index=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(20), nullable=False)
    marks = Column(Float, default=1.0)
    syllabus_area_tag = Column(String(100), nullable=True)
    course_code_tag = Column(String(20), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    is_active = Column(Boolean, default=True)
