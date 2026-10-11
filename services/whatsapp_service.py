"""
services/whatsapp_service.py
-----------------------------
Zero-cost, Meta-free WhatsApp Integration for Academy Mobile App:
- Direct 1-tap WhatsApp mobile dispatch (wa.me / WhatsApp deep-linking).
- Fee Reminders with dynamically embedded JazzCash / EasyPaisa / Bank Account details.
- Student Online Quiz invites with unique test links.
- Test scorecards dispatch to Parents upon test completion.
- Phone number cleaner for Pakistani (+92) and international formats.
"""

import re
import urllib.parse
from typing import Dict, Any, Optional
from database import Student, FeeRecord, OnlineTest, StudentSubmission, AcademySettings, SessionLocal


def clean_phone(phone: str, default_cc: str = "92") -> str:
    """Standardizes phone numbers for WhatsApp URL (digits only, no '+' sign)."""
    if not phone:
        return ""
    digits = re.sub(r"\D", "", phone.strip())
    if digits.startswith("00"):
        digits = digits[2:]
    elif digits.startswith("0") and len(digits) == 11:
        # Pakistani 03xx format
        digits = default_cc + digits[1:]
    return digits


class WhatsAppService:

    @staticmethod
    def get_whatsapp_url(phone: str, message: str) -> str:
        """Builds universal WhatsApp deep link for 1-tap dispatch from phone or PC."""
        cleaned = clean_phone(phone)
        encoded_text = urllib.parse.quote(message)
        return f"https://wa.me/{cleaned}?text={encoded_text}"

    @staticmethod
    def build_fee_reminder_message(
        fee_record: FeeRecord,
        settings: Optional[AcademySettings] = None,
    ) -> str:
        """
        Creates polite Roman Urdu message containing the student's dues
        PLUS the academy owner's saved JazzCash, EasyPaisa, and Bank details.
        """
        db = SessionLocal()
        try:
            if not settings:
                settings = db.query(AcademySettings).first()

            s = db.query(Student).filter(Student.id == fee_record.student_id).first() or fee_record.student
            due = fee_record.amount_due - fee_record.amount_paid
            due_str = f"PKR {due:,.0f}"

            msg = (
                f"🏫 *{settings.academy_name.upper()}*\n"
                f"*MAAHANA FEE ITTELA*\n\n"
                f"Mohtaram Walidain *{s.parent_name} Sahab*,\n\n"
                f"Umeed hai aap kheriyat se honge. {settings.academy_name} ki janib se "
                f"aap ke farzand/dukhtar ki fee ki baabat yaad-dehani karwai ja rahi hai:\n\n"
                f"👤 *Talib-e-Ilm (Student):* {s.name}\n"
                f"📚 *Class:* {s.grade}\n"
                f"🗓️ *Maheena:* {fee_record.month_year}\n"
                f"💰 *Baqaya Rakam:* *{due_str}*\n"
                f"📅 *Aakhri Tareekh:* {fee_record.due_date}\n\n"
                f"💳 *FEE JAMA KARWANE KA TARIQA (PAYMENT DETAILS):*\n"
                f"• *JazzCash:* {settings.jazzcash_number} ({settings.jazzcash_title})\n"
                f"• *EasyPaisa:* {settings.easypaisa_number} ({settings.easypaisa_title})\n"
                f"• *Bank Account:* {settings.bank_name}\n"
                f"   Account Title: {settings.bank_account_title}\n"
                f"   IBAN / Account #: {settings.bank_iban}\n\n"
                f"Barah-e-karam fee ada karne ke baad receipt/screenshot isi WhatsApp number par share farma dein.\n\n"
                f"Regards,\n"
                f"*{settings.academy_name}*\n"
                f"📞 {settings.academy_phone}"
            )
            return msg
        finally:
            db.close()

    @staticmethod
    def build_test_scorecard_message(
        submission: StudentSubmission,
        settings: Optional[AcademySettings] = None,
    ) -> str:
        """
        Builds test scorecard message for parents upon test completion.
        """
        db = SessionLocal()
        try:
            if not settings:
                settings = db.query(AcademySettings).first()

            s = db.query(Student).filter(Student.id == submission.student_id).first() or submission.student
            t = db.query(OnlineTest).filter(OnlineTest.id == submission.test_id).first() or submission.test

            msg = (
                f"📊 *{settings.academy_name.upper()}*\n"
                f"*ONLINE TEST KARKARDAGI REPORT*\n\n"
                f"Mohtaram Walidain *{s.parent_name} Sahab*,\n\n"
                f"Aap ke bache ki online test assessment report hasb-e-zail hai:\n\n"
                f"👤 *Student:* {s.name}\n"
                f"📚 *Class:* {s.grade}\n"
                f"📖 *Subject:* {t.subject}\n"
                f"📝 *Test:* {t.title}\n"
                f"-----------------------------------\n"
                f"🎯 *Hasil Karda Number:* {submission.total_obtained} / {t.total_marks}\n"
                f"📈 *Feesad (Percentage):* *{submission.percentage}%*\n"
                f"🏆 *Grade Awarded:* *{submission.grade}*\n"
                f"-----------------------------------\n"
                f"💡 *Teacher / AI Feedback:*\n{submission.ai_feedback[:250]}\n\n"
                f"Barah-e-karam bache ki taleemi taraqqi ka jaiza lein aur mazeed mehnat ki takeed farmaiye.\n\n"
                f"Regards,\n"
                f"*{settings.academy_name}*\n"
                f"📞 {settings.academy_phone}"
            )
            return msg
        finally:
            db.close()

    @staticmethod
    def build_quiz_invite_message(
        student: Student,
        test: OnlineTest,
        quiz_url: str,
        settings: Optional[AcademySettings] = None,
    ) -> str:
        """
        Builds WhatsApp invite with test link sent to the student.
        """
        name = settings.academy_name if settings else "THE LAHORE ACADAMY JHANG"
        return (
            f"📝 *{name.upper()} - ONLINE ASSESSMENT*\n\n"
            f"Assalam-o-Alaikum *{student.name}* ({student.grade}),\n\n"
            f"Aap ka *{test.subject}* ka online test activate ho chuka hai:\n"
            f"📋 *Test Title:* {test.title}\n"
            f"⏳ *Waqt (Duration):* {test.duration_minutes} Minutes\n"
            f"🎯 *Total Marks:* {test.total_marks}\n\n"
            f"Barah-e-karam test shuru karne ke liye is link par click karein:\n"
            f"👉 {quiz_url}\n\n"
            f"Test mukammal hone ke baad apna scorecard foran check karein. Best of luck!\n\n"
            f"Regards,\n"
            f"*{name}*"
        )
