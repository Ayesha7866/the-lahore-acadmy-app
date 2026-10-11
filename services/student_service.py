"""
services/student_service.py
---------------------------
Student business logic for the Academy Mobile App.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import Student, SessionLocal


class StudentService:

    @staticmethod
    def list_students(grade: Optional[str] = None, search: Optional[str] = None) -> List[Student]:
        db = SessionLocal()
        try:
            query = db.query(Student).filter(Student.is_active == True)
            if grade and grade != "All Classes":
                query = query.filter(Student.grade == grade)
            if search:
                term = f"%{search.strip().lower()}%"
                query = query.filter(
                    (func.lower(Student.name).like(term)) |
                    (func.lower(Student.roll_number).like(term)) |
                    (func.lower(Student.parent_name).like(term))
                )
            return query.order_by(Student.grade, Student.roll_number).all()
        finally:
            db.close()

    @staticmethod
    def get_student(student_id: int) -> Optional[Student]:
        db = SessionLocal()
        try:
            return db.query(Student).filter(Student.id == student_id).first()
        finally:
            db.close()

    @staticmethod
    def create_student(
        name: str,
        grade: str,
        student_phone: str,
        parent_name: str,
        parent_phone: str,
        monthly_fee: float = 5000.0,
        subjects: str = "Science, Mathematics, English, Computer Science",
    ) -> Student:
        db = SessionLocal()
        try:
            clean_g = grade.replace(" ", "").replace("st", "").replace("nd", "").replace("th", "")
            count = db.query(Student).filter(Student.grade == grade).count() + 1
            roll = f"ACAD-{clean_g}-{count:03d}"

            student = Student(
                roll_number=roll,
                name=name.strip(),
                grade=grade,
                subjects=subjects,
                student_phone=student_phone.strip(),
                parent_name=parent_name.strip(),
                parent_phone=parent_phone.strip(),
                monthly_fee=float(monthly_fee),
                fee_status="Pending",
            )
            db.add(student)
            db.commit()
            db.refresh(student)
            return student
        finally:
            db.close()

    @staticmethod
    def update_student(student_id: int, **kwargs) -> Optional[Student]:
        db = SessionLocal()
        try:
            student = db.query(Student).filter(Student.id == student_id).first()
            if not student:
                return None
            for k, v in kwargs.items():
                if hasattr(student, k) and v is not None:
                    setattr(student, k, v)
            db.commit()
            db.refresh(student)
            return student
        finally:
            db.close()

    @staticmethod
    def delete_student(student_id: int) -> bool:
        db = SessionLocal()
        try:
            student = db.query(Student).filter(Student.id == student_id).first()
            if not student:
                return False
            db.delete(student)
            db.commit()
            return True
        finally:
            db.close()
