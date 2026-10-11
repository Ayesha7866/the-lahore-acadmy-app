"""
seed_data.py
------------
Seeds the SQLite database with realistic Pakistani students, fee invoices,
and sample online tests (MCQs + Short questions) for 9th, 10th, 1st Year, and 2nd Year.
"""

from database import init_db, SessionLocal, Student, FeeRecord, OnlineTest, TestQuestion, AcademySettings
from services.student_service import StudentService
from services.fee_service import FeeService
from services.test_service import TestService


def seed_mobile_database():
    init_db()
    db = SessionLocal()
    try:
        if db.query(Student).count() > 0:
            return  # Already seeded

        print("🌱 Seeding Mobile Academy Database...")

        # 1. Update Payment Gateways
        settings = db.query(AcademySettings).first()
        if settings:
            settings.academy_name = "THE LAHORE ACADAMY JHANG"
            settings.academy_phone = "+923001234567"
            settings.jazzcash_number = "03001234567"
            settings.jazzcash_title = "THE LAHORE ACADAMY JHANG"
            settings.easypaisa_number = "03007654321"
            settings.easypaisa_title = "THE LAHORE ACADAMY JHANG"
            settings.bank_name = "Meezan Bank"
            settings.bank_account_title = "THE LAHORE ACADAMY JHANG"
            settings.bank_iban = "PK12MEZN0001234567890123"
            db.commit()

        # 2. Add Sample Students across all 4 tiers
        sample_students = [
            {"name": "Ali Khan", "grade": "10th", "s_phone": "03001112233", "p_name": "Tariq Khan", "p_phone": "03005551122", "fee": 6000.0},
            {"name": "Fatima Zahra", "grade": "9th", "s_phone": "03023334455", "p_name": "Muhammad Zahid", "p_phone": "03025553344", "fee": 5000.0},
            {"name": "Hamza Ahmed", "grade": "1st Year", "s_phone": "03045556677", "p_name": "Ahmed Raza", "p_phone": "03045555566", "fee": 7000.0},
            {"name": "Ayesha Noor", "grade": "2nd Year", "s_phone": "03067778899", "p_name": "Noor Muhammad", "p_phone": "03065557788", "fee": 7500.0},
            {"name": "Bilal Hassan", "grade": "10th", "s_phone": "03012223344", "p_name": "Hassan Mehmood", "p_phone": "03015552233", "fee": 6000.0},
        ]

        for s in sample_students:
            StudentService.create_student(
                name=s["name"],
                grade=s["grade"],
                student_phone=s["s_phone"],
                parent_name=s["p_name"],
                parent_phone=s["p_phone"],
                monthly_fee=s["fee"],
            )

        # 3. Generate Fee Invoices for this month
        FeeService.generate_monthly_invoices("October 2026")

        # 4. Create an Online Test with MCQs and Short Questions for 10th Grade Mathematics & Science
        test = TestService.create_test(
            title="10th Mathematics & Physics Midterm",
            grade="10th",
            subject="Mathematics",
            duration_minutes=25,
            total_marks=20.0,
        )

        # Add MCQ 1
        TestService.add_question(
            test_id=test.id,
            question_type="mcq",
            question_text="What is the quadratic formula to solve ax² + bx + c = 0?",
            marks=5.0,
            option_a="x = (-b ± √(b² - 4ac)) / (2a)",
            option_b="x = (-b ± √(b² + 4ac)) / (2a)",
            option_c="x = (b ± √(b² - 4ac)) / (2a)",
            option_d="x = -b / (2a)",
            correct_answer="A",
        )

        # Add MCQ 2
        TestService.add_question(
            test_id=test.id,
            question_type="mcq",
            question_text="Which law states that force equals mass multiplied by acceleration (F = ma)?",
            marks=5.0,
            option_a="Newton's First Law",
            option_b="Newton's Second Law",
            option_c="Newton's Third Law",
            option_d="Law of Universal Gravitation",
            correct_answer="B",
        )

        # Add Short Question
        TestService.add_question(
            test_id=test.id,
            question_type="short",
            question_text="State Archimedes' Principle and explain how an iron ship floats on water.",
            marks=10.0,
            correct_answer="When a body is immersed in a liquid, it experiences an upward buoyant force equal to the weight of the fluid displaced. A hollow iron ship displaces a large volume of water whose weight is greater than the ship's weight, allowing it to float.",
        )

        print("✅ Mobile database seeded successfully with students, fees, and online tests!")

    finally:
        db.close()


if __name__ == "__main__":
    seed_mobile_database()
