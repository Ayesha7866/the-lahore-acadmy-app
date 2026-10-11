"""
services/fee_service.py
-----------------------
Fee management, payment gateway configuration, and receipt generation.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from database import Student, FeeRecord, AcademySettings, SessionLocal


class FeeService:

    @staticmethod
    def get_settings() -> AcademySettings:
        db = SessionLocal()
        try:
            settings = db.query(AcademySettings).first()
            if not settings:
                settings = AcademySettings()
                db.add(settings)
                db.commit()
                db.refresh(settings)
            return settings
        finally:
            db.close()

    @staticmethod
    def update_settings(**kwargs) -> AcademySettings:
        db = SessionLocal()
        try:
            settings = db.query(AcademySettings).first()
            if not settings:
                settings = AcademySettings()
                db.add(settings)
            for k, v in kwargs.items():
                if hasattr(settings, k) and v is not None:
                    setattr(settings, k, v)
            db.commit()
            db.refresh(settings)
            return settings
        finally:
            db.close()

    @staticmethod
    def generate_monthly_invoices(month_year: Optional[str] = None) -> int:
        db = SessionLocal()
        try:
            if not month_year:
                month_year = datetime.now().strftime("%B %Y")
            students = db.query(Student).filter(Student.is_active == True).all()
            count = 0
            for s in students:
                existing = db.query(FeeRecord).filter(
                    FeeRecord.student_id == s.id,
                    FeeRecord.month_year == month_year,
                ).first()
                if not existing:
                    rec = FeeRecord(
                        student_id=s.id,
                        month_year=month_year,
                        amount_due=s.monthly_fee,
                        amount_paid=0.0,
                        due_date=datetime.now().strftime("%Y-%m-10"),
                        status="Pending",
                    )
                    db.add(rec)
                    s.fee_status = "Pending"
                    count += 1
            db.commit()
            return count
        finally:
            db.close()

    @staticmethod
    def mark_as_paid(fee_record_id: int) -> Optional[FeeRecord]:
        """Marks fee record as Paid and generates a unique digital receipt."""
        db = SessionLocal()
        try:
            record = db.query(FeeRecord).filter(FeeRecord.id == fee_record_id).first()
            if not record:
                return None
            record.amount_paid = record.amount_due
            record.status = "Paid"
            record.payment_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            record.receipt_number = f"REC-{datetime.now().strftime('%y%m')}-{record.id:04d}"

            # Check if student has other pending records
            other = db.query(FeeRecord).filter(
                FeeRecord.student_id == record.student_id,
                FeeRecord.status == "Pending",
                FeeRecord.id != record.id,
            ).first()
            if not other:
                record.student.fee_status = "Paid"

            db.commit()
            db.refresh(record)
            return record
        finally:
            db.close()

    @staticmethod
    def list_fee_records(status_filter: Optional[str] = None) -> List[FeeRecord]:
        db = SessionLocal()
        try:
            query = db.query(FeeRecord).join(Student)
            if status_filter and status_filter != "All":
                query = query.filter(FeeRecord.status == status_filter)
            return query.order_by(FeeRecord.id.desc()).all()
        finally:
            db.close()

    @staticmethod
    def get_financial_summary() -> Dict[str, Any]:
        db = SessionLocal()
        try:
            records = db.query(FeeRecord).all()
            total_due = sum(r.amount_due for r in records)
            total_collected = sum(r.amount_paid for r in records)
            pending_amount = max(0.0, total_due - total_collected)
            pending_count = sum(1 for r in records if r.status == "Pending")
            paid_count = sum(1 for r in records if r.status == "Paid")
            rate = (total_collected / total_due * 100) if total_due > 0 else 0.0

            return {
                "total_due": total_due,
                "total_collected": total_collected,
                "pending_amount": pending_amount,
                "pending_count": pending_count,
                "paid_count": paid_count,
                "recovery_rate": round(rate, 1),
            }
        finally:
            db.close()
