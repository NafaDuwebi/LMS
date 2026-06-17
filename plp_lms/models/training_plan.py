from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Date
from sqlalchemy.sql import func
from database import Base


class TrainingPlan(Base):
    __tablename__ = "training_plans"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class TrainingPlanItem(Base):
    __tablename__ = "training_plan_items"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("training_plans.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    due_within_days = Column(Integer, default=30)
    is_mandatory = Column(Boolean, default=True)


class TrainingPlanAssignment(Base):
    __tablename__ = "training_plan_assignments"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("training_plans.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_string = Column(String(20), nullable=True)
    assigned_at = Column(DateTime, server_default=func.now())
    due_date = Column(Date, nullable=True)
