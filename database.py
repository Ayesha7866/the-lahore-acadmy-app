"""
database.py
-----------
SQLite Database models & connection for the Academy Mobile App (Flet).
Stores students, payment settings, fee ledgers, online tests, questions, and submissions.
"""

import json
from datetime import datetime
from pathlib import Path
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DB_PATH = Path(__file__).resolve().parent / "academy_mobile.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class AcademySettings(Base):
    """Stores academy owner details, payment gateways (JazzCash/EasyPaisa/Bank), and API keys."""
    __tablename__ = "academy_settings"

    id = Column(Integer, primary_key=True)
    academy_name = Column(String(150), default="THE LAHORE ACADAMY JHANG")
    academy_phone = Column(String(50), default="+923001234567")
    owner_name = Column(String(100), default="Academy Admin")
    
    # Payment Gateway Settings
    jazzcash_number = Column(String(50), default="03001234567")
    jazzcash_title = Column(String(100), default="Al-Hikmah Academy")
    easypaisa_number = Column(String(50), default="03001234567")
    easypaisa_title = Column(String(100), default="Al-Hikmah Academy")
    bank_name = Column(String(100), default="Meezan Bank")
    bank_account_title = Column(String(100), default="Al-Hikmah Academy Admin")
    bank_iban = Column(String(100), default="PK12MEZN0001234567890123")
    
    # AI & Quiz Server
    gemini_api_key = Column(String(150), default="")
    quiz_server_host = Column(String(50), default="127.0.0.1")
    quiz_server_port = Column(Integer, default=8000)


class Student(Base):
    """Enrolled student details."""
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    roll_number = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), index=True, nullable=False)
    grade = Column(String(50), nullable=False)  # 9th, 10th, 1st Year, 2nd Year
    subjects = Column(String(255), default="Science, Mathematics, English, Computer Science")
    student_phone = Column(String(30), nullable=False)
    parent_name = Column(String(100), nullable=False)
    parent_phone = Column(String(30), nullable=False)
    monthly_fee = Column(Float, default=5000.0)
    fee_status = Column(String(30), default="Pending")  # Paid, Pending
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    fee_records = relationship("FeeRecord", back_populates="student", cascade="all, delete-orphan")
    submissions = relationship("StudentSubmission", back_populates="student", cascade="all, delete-orphan")


class FeeRecord(Base):
    """Monthly fee invoice and payment receipt."""
    __tablename__ = "fee_records"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    month_year = Column(String(50), nullable=False)  # e.g., "October 2026"
    amount_due = Column(Float, nullable=False)
    amount_paid = Column(Float, default=0.0)
    due_date = Column(String(30), nullable=False)  # e.g., "2026-10-15"
    status = Column(String(30), default="Pending")  # Paid, Pending
    receipt_number = Column(String(50), nullable=True)
    payment_date = Column(String(30), nullable=True)

    student = relationship("Student", back_populates="fee_records")


class OnlineTest(Base):
    """Online quiz/exam configuration."""
    __tablename__ = "online_tests"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)  # e.g. "Maths Chapter 1 Unit Test"
    grade = Column(String(50), nullable=False)  # 9th, 10th, 1st Year, 2nd Year
    subject = Column(String(100), nullable=False)  # Science, Mathematics, English, Computer Science
    duration_minutes = Column(Integer, default=30)
    total_marks = Column(Float, default=50.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    questions = relationship("TestQuestion", back_populates="test", cascade="all, delete-orphan")
    submissions = relationship("StudentSubmission", back_populates="test", cascade="all, delete-orphan")


class TestQuestion(Base):
    """Individual MCQ or Short Question for an Online Test."""
    __tablename__ = "test_questions"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("online_tests.id"), nullable=False, index=True)
    question_type = Column(String(20), default="mcq")  # "mcq" or "short"
    question_text = Column(Text, nullable=False)
    option_a = Column(String(255), nullable=True)
    option_b = Column(String(255), nullable=True)
    option_c = Column(String(255), nullable=True)
    option_d = Column(String(255), nullable=True)
    correct_answer = Column(String(255), nullable=True)  # For MCQ: 'A', 'B', 'C', 'D'. For short: model answer
    marks = Column(Float, default=5.0)

    test = relationship("OnlineTest", back_populates="questions")


class StudentSubmission(Base):
    """Online test submission submitted by a student via the web link."""
    __tablename__ = "student_submissions"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("online_tests.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    answers_json = Column(Text, nullable=False)  # JSON dictionary of question_id: answer
    mcq_marks = Column(Float, default=0.0)
    short_marks = Column(Float, default=0.0)
    total_obtained = Column(Float, default=0.0)
    percentage = Column(Float, default=0.0)
    grade = Column(String(10), default="F")
    ai_feedback = Column(Text, default="")
    submitted_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(30), default="Graded")  # "Graded", "Pending Review"

    test = relationship("OnlineTest", back_populates="submissions")
    student = relationship("Student", back_populates="submissions")


def init_db():
    """Initializes tables and default academy settings."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        settings = db.query(AcademySettings).first()
        if not settings:
            settings = AcademySettings()
            db.add(settings)
            db.commit()
    finally:
        db.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
