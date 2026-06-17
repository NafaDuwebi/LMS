from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class MaterialView(Base):
    __tablename__ = "material_views"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    viewed_at = Column(DateTime, server_default=func.now(), nullable=False)
    view_duration_seconds = Column(Integer, default=0)

    user = relationship("User", foreign_keys=[user_id])
    material = relationship("Material", foreign_keys=[material_id])
