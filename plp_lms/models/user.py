from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Date, Float, Index, text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("uq_users_email_ci", text("LOWER(email)"), unique=True),
    )

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="learner")
    full_name = Column(String(255), nullable=False)
    organisation = Column(String(255), nullable=True)
    job_title = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    cohort_token = Column(String(100), nullable=True)
    setup_token_expiry = Column(DateTime, nullable=True)
    reset_token = Column(String(100), nullable=True)
    reset_token_expiry = Column(DateTime, nullable=True)
    reasonable_adjustments = Column(Text, nullable=True)
    gdpr_consent_date = Column(DateTime, nullable=True)
    data_retention_flag = Column(Boolean, default=True)
    force_password_change = Column(Boolean, default=False)
    requires_gdpr_consent = Column(Boolean, default=False)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    notification_preferences = Column(Text, default="{}")
    token_version = Column(Integer, default=0)

    department = relationship("Department", foreign_keys=[department_id], lazy="joined")
