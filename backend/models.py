from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from database import Base

class ProjectRequest(Base):
    __tablename__ = "project_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    project_description = Column(Text, nullable=False)
    budget = Column(String, nullable=True)
    timeline = Column(String, nullable=True)
    project_type = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending, in_progress, completed, rejected
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)

