from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.db import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    college = Column(String, nullable=True)
    branch = Column(String, nullable=True)
    year = Column(Integer, nullable=True)
    phone = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    linkedin = Column(String, nullable=True)
    github = Column(String, nullable=True)
    avatar_color = Column(String, default="#6366f1")
    total_xp = Column(Integer, default=0)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    test_attempts = relationship("TestAttempt", back_populates="user")
    drive_dates = relationship("DriveDate", back_populates="user")


class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, nullable=False)
    difficulty = Column(String, default="medium")
    question_text = Column(Text, nullable=False)
    options = Column(JSON, nullable=True)
    correct_answer = Column(String, nullable=False)
    explanation = Column(Text, nullable=True)
    starter_code = Column(Text, nullable=True)
    test_cases = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CompanyQuestion(Base):
    __tablename__ = "company_questions"
    id = Column(Integer, primary_key=True, index=True)
    company = Column(String, nullable=False, index=True)
    category = Column(String, nullable=False)
    difficulty = Column(String, default="medium")
    question_text = Column(Text, nullable=False)
    options = Column(JSON, nullable=True)
    correct_answer = Column(String, nullable=False)
    explanation = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)
    year = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TestAttempt(Base):
    __tablename__ = "test_attempts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    test_type = Column(String, nullable=False)
    score = Column(Float, nullable=True)
    max_score = Column(Float, nullable=True)
    percentage = Column(Float, nullable=True)
    time_taken = Column(Integer, nullable=True)
    answers = Column(JSON, nullable=True)
    feedback = Column(Text, nullable=True)
    xp_earned = Column(Integer, default=0)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    user = relationship("User", back_populates="test_attempts")


class CommunicationAttempt(Base):
    __tablename__ = "communication_attempts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    transcript = Column(Text, nullable=True)
    topic = Column(String, nullable=True)
    words_per_minute = Column(Float, nullable=True)
    filler_word_count = Column(Integer, nullable=True)
    fluency_score = Column(Float, nullable=True)
    overall_score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DriveDate(Base):
    __tablename__ = "drive_dates"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company = Column(String, nullable=False)
    drive_date = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="drive_dates")
