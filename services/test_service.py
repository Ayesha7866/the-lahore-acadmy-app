"""
services/test_service.py
------------------------
Online test authoring and management: MCQs, Short Questions, and test links.
"""

from typing import List, Optional, Dict, Any
from database import OnlineTest, TestQuestion, StudentSubmission, Student, AcademySettings, SessionLocal


class TestService:

    @staticmethod
    def create_test(
        title: str,
        grade: str,
        subject: str,
        duration_minutes: int = 30,
        total_marks: float = 50.0,
    ) -> OnlineTest:
        db = SessionLocal()
        try:
            test = OnlineTest(
                title=title.strip(),
                grade=grade,
                subject=subject,
                duration_minutes=int(duration_minutes),
                total_marks=float(total_marks),
            )
            db.add(test)
            db.commit()
            db.refresh(test)
            return test
        finally:
            db.close()

    @staticmethod
    def add_question(
        test_id: int,
        question_type: str,
        question_text: str,
        marks: float = 5.0,
        option_a: Optional[str] = None,
        option_b: Optional[str] = None,
        option_c: Optional[str] = None,
        option_d: Optional[str] = None,
        correct_answer: Optional[str] = None,
    ) -> TestQuestion:
        db = SessionLocal()
        try:
            q = TestQuestion(
                test_id=test_id,
                question_type=question_type,
                question_text=question_text.strip(),
                marks=float(marks),
                option_a=option_a.strip() if option_a else None,
                option_b=option_b.strip() if option_b else None,
                option_c=option_c.strip() if option_c else None,
                option_d=option_d.strip() if option_d else None,
                correct_answer=correct_answer.strip() if correct_answer else None,
            )
            db.add(q)
            db.commit()
            db.refresh(q)
            return q
        finally:
            db.close()

    @staticmethod
    def list_tests(grade: Optional[str] = None) -> List[OnlineTest]:
        db = SessionLocal()
        try:
            query = db.query(OnlineTest)
            if grade and grade != "All Classes":
                query = query.filter(OnlineTest.grade == grade)
            return query.order_by(OnlineTest.id.desc()).all()
        finally:
            db.close()

    @staticmethod
    def get_test(test_id: int) -> Optional[OnlineTest]:
        db = SessionLocal()
        try:
            return db.query(OnlineTest).filter(OnlineTest.id == test_id).first()
        finally:
            db.close()

    @staticmethod
    def generate_quiz_url(test_id: int, student_id: int) -> str:
        """Constructs web link that students open on WhatsApp."""
        db = SessionLocal()
        try:
            settings = db.query(AcademySettings).first()
            host = settings.quiz_server_host if settings else "127.0.0.1"
            port = settings.quiz_server_port if settings else 8000
            return f"http://{host}:{port}/quiz/{test_id}?sid={student_id}"
        finally:
            db.close()

    @staticmethod
    def list_submissions(test_id: Optional[int] = None) -> List[StudentSubmission]:
        db = SessionLocal()
        try:
            query = db.query(StudentSubmission).join(Student).join(OnlineTest)
            if test_id:
                query = query.filter(StudentSubmission.test_id == test_id)
            return query.order_by(StudentSubmission.id.desc()).all()
        finally:
            db.close()
