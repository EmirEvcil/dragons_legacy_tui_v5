"""
Security Question model for Legend of Dragon's Legacy
"""

from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from dragons_legacy.database import Base


class SecurityQuestion(Base):
    __tablename__ = "security_questions"

    id = Column(Integer, primary_key=True, index=True)
    question_text = Column(String(500), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    users = relationship("User", back_populates="security_question")

    def __repr__(self):
        return f"<SecurityQuestion(id={self.id}, question='{self.question_text[:50]}...')>"


# Predefined security questions
PREDEFINED_SECURITY_QUESTIONS = [
    "What was the name of your first pet?",
    "What is your mother's maiden name?",
    "What was the name of your first school?",
    "What city were you born in?",
    "What is your favorite childhood memory location?"
]