"""
User model for Legend of Dragon's Legacy
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from dragons_legacy.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Security question fields
    security_question_id = Column(Integer, ForeignKey("security_questions.id"))
    security_answer_hash = Column(String(255))
    
    # Relationships
    security_question = relationship("SecurityQuestion", back_populates="users")
    characters = relationship("Character", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"