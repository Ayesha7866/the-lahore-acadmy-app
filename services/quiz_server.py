"""
services/quiz_server.py
-----------------------
Lightweight embedded web server that serves student quiz pages.
Students open the link in WhatsApp without installing any app.
Submissions are auto-graded and saved directly into the SQLite database.
"""

import threading
import json
import logging
from typing import Optional
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
import uvicorn

from database import SessionLocal, OnlineTest, Student, StudentSubmission, AcademySettings
from services.ai_grading_service import AIGradingService

quiz_app = FastAPI(title="Academy Student Quiz Portal")
logger = logging.getLogger("QuizServer")


@quiz_app.get("/quiz/{test_id}", response_class=HTMLResponse)
def get_quiz_page(test_id: int, sid: Optional[int] = None):
    """Renders the mobile-responsive quiz interface for students."""
    db = SessionLocal()
    try:
        test = db.query(OnlineTest).filter(OnlineTest.id == test_id).first()
        student = db.query(Student).filter(Student.id == sid).first() if sid else None
        settings = db.query(AcademySettings).first()

        if not test:
            return HTMLResponse("<h2>Error: Test not found or has expired.</h2>", status_code=404)

        student_name = student.name if student else "Guest Student"
        student_grade = student.grade if student else test.grade
        student_id_val = student.id if student else 1

        # Check if already submitted
        if student:
            existing = db.query(StudentSubmission).filter(
                StudentSubmission.test_id == test.id,
                StudentSubmission.student_id == student.id,
            ).first()
            if existing:
                return HTMLResponse(f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Result - {test.title}</title>
                    <style>
                        body {{ font-family: sans-serif; background: #0f172a; color: #f8fafc; padding: 20px; text-align: center; }}
                        .card {{ background: #1e293b; padding: 30px; border-radius: 16px; max-width: 450px; margin: 40px auto; }}
                        .score {{ font-size: 2.5rem; font-weight: bold; color: #38bdf8; margin: 15px 0; }}
                        .badge {{ display: inline-block; padding: 6px 14px; border-radius: 20px; background: #0ea5e9; font-weight: bold; }}
                    </style>
                </head>
                <body>
                    <div class="card">
                        <h2>Assessment Already Submitted</h2>
                        <p style="color: #94a3b8;">{student.name} ({student.grade})</p>
                        <div class="score">{existing.total_obtained} / {test.total_marks}</div>
                        <p><span class="badge">Grade: {existing.grade} ({existing.percentage}%)</span></p>
                        <p style="margin-top: 20px; font-size: 0.9rem; color: #cbd5e1;">A copy of your performance has been delivered to your parent's WhatsApp.</p>
                    </div>
                </body>
                </html>
                """)

        # Generate Question Forms
        questions_html = ""
        for idx, q in enumerate(test.questions, 1):
            if q.question_type == "mcq":
                opts_html = f"""
                <div class="options">
                    <label class="opt-label"><input type="radio" name="q_{q.id}" value="A" required> A) {q.option_a}</label>
                    <label class="opt-label"><input type="radio" name="q_{q.id}" value="B"> B) {q.option_b}</label>
                    <label class="opt-label"><input type="radio" name="q_{q.id}" value="C"> C) {q.option_c}</label>
                    <label class="opt-label"><input type="radio" name="q_{q.id}" value="D"> D) {q.option_d}</label>
                </div>
                """
            else:
                opts_html = f"""
                <div style="margin-top: 10px;">
                    <textarea name="q_{q.id}" rows="3" class="text-input" placeholder="Type your answer clearly here..." required></textarea>
                </div>
                """

            questions_html += f"""
            <div class="question-box">
                <div class="q-header">
                    <span class="q-num">Question {idx}</span>
                    <span class="q-marks">{q.marks} Marks ({q.question_type.upper()})</span>
                </div>
                <div class="q-text">{q.question_text}</div>
                {opts_html}
            </div>
            """

        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{test.title} - {settings.academy_name}</title>
            <style>
                * {{ box-sizing: border-box; margin:0; padding:0; }}
                body {{ background-color: #0b1120; color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 15px; }}
                .container {{ max-width: 550px; margin: 0 auto; padding-bottom: 50px; }}
                .header-card {{ background: linear-gradient(135deg, #1e293b, #0f172a); border: 1px solid #334155; border-radius: 14px; padding: 18px; margin-bottom: 20px; }}
                .academy-name {{ font-size: 0.85rem; color: #38bdf8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }}
                .test-title {{ font-size: 1.35rem; font-weight: 800; margin: 6px 0; color: #fff; }}
                .meta-tags {{ display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; }}
                .pill {{ background: #1e293b; border: 1px solid #475569; padding: 4px 10px; border-radius: 6px; font-size: 0.78rem; font-weight: 600; color: #94a3b8; }}
                .question-box {{ background: #131d31; border: 1px solid #23324d; border-radius: 12px; padding: 16px; margin-bottom: 16px; }}
                .q-header {{ display: flex; justify-content: space-between; font-size: 0.8rem; font-weight: 700; margin-bottom: 8px; }}
                .q-num {{ color: #38bdf8; }}
                .q-marks {{ color: #a5b4fc; }}
                .q-text {{ font-size: 0.98rem; line-height: 1.45; font-weight: 500; margin-bottom: 12px; }}
                .options {{ display: flex; flex-direction: column; gap: 8px; }}
                .opt-label {{ display: flex; align-items: center; gap: 10px; background: #1c273e; padding: 10px 14px; border-radius: 8px; cursor: pointer; border: 1px solid transparent; font-size: 0.9rem; }}
                .opt-label:hover {{ border-color: #38bdf8; background: #22304d; }}
                .text-input {{ width: 100%; background: #0b1120; border: 1px solid #334155; border-radius: 8px; color: #fff; padding: 10px; font-family: inherit; font-size: 0.9rem; }}
                .text-input:focus {{ outline: none; border-color: #38bdf8; }}
                .submit-btn {{ width: 100%; background: #2563eb; color: #fff; border: none; padding: 14px; border-radius: 10px; font-size: 1.05rem; font-weight: 700; cursor: pointer; margin-top: 10px; box-shadow: 0 4px 12px rgba(37,99,235,0.4); }}
                .submit-btn:hover {{ background: #1d4ed8; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header-card">
                    <div class="academy-name">{settings.academy_name}</div>
                    <div class="test-title">{test.title}</div>
                    <div class="meta-tags">
                        <span class="pill">👤 {student_name}</span>
                        <span class="pill">📚 {student_grade}</span>
                        <span class="pill">📖 {test.subject}</span>
                        <span class="pill">⏱️ {test.duration_minutes} Mins</span>
                    </div>
                </div>

                <form method="POST" action="/quiz/{test.id}/submit">
                    <input type="hidden" name="student_id" value="{student_id_val}">
                    {questions_html}
                    <button type="submit" class="submit-btn">Submit Exam 🚀</button>
                </form>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(html_content)

    finally:
        db.close()


@quiz_app.post("/quiz/{test_id}/submit", response_class=HTMLResponse)
async def submit_quiz(test_id: int, request: Request):
    """Processes student submission and triggers AI & MCQ auto-grading."""
    form_data = await request.form()
    student_id = int(form_data.get("student_id", 1))

    # Parse questions answers
    answers = {}
    for key, val in form_data.items():
        if key.startswith("q_"):
            answers[key] = str(val)

    submission = AIGradingService.grade_submission(
        test_id=test_id,
        student_id=student_id,
        student_answers=answers,
    )

    db = SessionLocal()
    try:
        test = db.query(OnlineTest).filter(OnlineTest.id == test_id).first()
        student = db.query(Student).filter(Student.id == student_id).first()
        settings = db.query(AcademySettings).first()

        score_badge = "color: #10b981;" if submission.percentage >= 70 else "color: #f59e0b;" if submission.percentage >= 50 else "color: #ef4444;"

        feedback_lines = "".join([f"<li style='margin-bottom:6px;'>{line}</li>" for line in submission.ai_feedback.splitlines() if line.strip()])

        result_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Exam Result - {student.name}</title>
            <style>
                body {{ background: #0b1120; color: #f8fafc; font-family: sans-serif; padding: 20px; }}
                .card {{ max-width: 500px; margin: 30px auto; background: #1e293b; border-radius: 16px; padding: 25px; border: 1px solid #334155; text-align: center; }}
                .score {{ font-size: 3rem; font-weight: 800; {score_badge} margin: 15px 0; }}
                .grade-pill {{ background: #0f172a; padding: 6px 16px; border-radius: 20px; font-weight: 700; display: inline-block; font-size: 1.1rem; border: 1px solid #475569; }}
                .breakdown {{ text-align: left; background: #0f172a; border-radius: 10px; padding: 15px; margin-top: 20px; font-size: 0.85rem; color: #cbd5e1; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h3 style="color: #38bdf8; text-transform: uppercase;">{settings.academy_name}</h3>
                <h2 style="margin: 10px 0;">🎉 Exam Submitted!</h2>
                <p style="color: #94a3b8;">Student: <b>{student.name}</b> ({student.grade})</p>
                <div class="score">{submission.total_obtained} / {test.total_marks}</div>
                <div class="grade-pill">Grade: {submission.grade} ({submission.percentage}%)</div>
                
                <div class="breakdown">
                    <h4 style="color: #fff; margin-bottom: 8px;">Evaluation Details:</h4>
                    <ul style="padding-left: 20px;">
                        {feedback_lines}
                    </ul>
                </div>

                <p style="margin-top: 25px; font-size: 0.85rem; color: #64748b;">
                    Your performance scorecard has been automatically prepared for WhatsApp dispatch to your parents.
                </p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(result_html)
    finally:
        db.close()


def start_quiz_server_thread(host: str = "0.0.0.0", port: int = 8000):
    """Launches the quiz server in a daemon thread so it runs seamlessly in the mobile app."""
    def run():
        uvicorn.run(quiz_app, host=host, port=port, log_level="warning")

    server_thread = threading.Thread(target=run, daemon=True)
    server_thread.start()
    return server_thread
