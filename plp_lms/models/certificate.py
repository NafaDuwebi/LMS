from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    enrolment_id = Column(Integer, ForeignKey("enrolments.id"), nullable=True)
    issued_at = Column(DateTime, server_default=func.now())
    expiry_date = Column(DateTime, nullable=True)
    certificate_number = Column(String(40), unique=True, nullable=False)
    pdf_path = Column(String(500), nullable=True)
    revoked = Column(Boolean, default=False)
    revoked_reason = Column(Text, nullable=True)
    revoked_at = Column(DateTime, nullable=True)

    user = relationship("User", foreign_keys=[user_id])
    course = relationship("Course", back_populates="certificates")
