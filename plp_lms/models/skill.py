from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    how_to_demonstrate = Column(Text, nullable=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    claims = relationship("SkillClaim", back_populates="skill", cascade="all, delete-orphan")


class SkillClaim(Base):
    __tablename__ = "skill_claims"

    id = Column(Integer, primary_key=True, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    claim_comment = Column(Text, nullable=True)
    evidence_path = Column(String(500), nullable=True)
    status = Column(String(20), default="pending")
    reviewer_comment = Column(Text, nullable=True)
    submitted_at = Column(DateTime, server_default=func.now())
    reviewed_at = Column(DateTime, nullable=True)

    skill = relationship("Skill", back_populates="claims")
    user = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])
