from sqlalchemy.orm import relationship
from app.models.database import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func

class UserPrivacy(Base):
    __tablename__ = "exordium_users_privacy"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("exordium_users.id", ondelete="CASCADE"), unique=True, nullable=False)
    user_password = Column(String(255), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    last_changed_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    user = relationship("User", back_populates="privacy", lazy="joined")

