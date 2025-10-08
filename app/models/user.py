from sqlalchemy.orm import relationship
from app.models.database import Base
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

class User(Base):
    __tablename__ = "exordium_users"

    id = Column(Integer, primary_key=True, index=True)
    google_id = Column(String(255), unique=True, index=True, nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=True)
    pict_uri = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    refresh_tokens = relationship("UserRefreshToken", back_populates="user", cascade="all, delete-orphan")
