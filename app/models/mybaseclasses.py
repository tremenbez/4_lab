from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    login_history = relationship("LoginHistory", back_populates="user")

class LoginHistory(Base):
    __tablename__ = "login_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user_agent = Column(String)
    login_time = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="login_history")