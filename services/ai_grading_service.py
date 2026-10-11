"""
services/ai_grading_service.py
------------------------------
Hybrid Auto-Grading Suite:
1. Instant deterministic MCQ evaluation.
2. Short answer grading via Google Gemini AI (with intelligent semantic fallback).
3. Automatic percentage, letter grade (A+ to F), and feedback generation.
"""

import json
import re
from typing import Dict, Any, List
from database import OnlineTest, TestQuestion, StudentSubmission, Student, AcademySettings, SessionLocal


def compute_grade_letter(percentage: float) -> str:
    if percentage >= 90.0:
        return "A+"
    elif percentage >= 80.0:
        return "A"
    elif percentage >= 70.0:
        return "B"
    elif percentage >= 60.0:
        return "C"
    elif percentage >= 50.0:
        return "D"
    return "F"


class AIGradingService:

    @staticmethod
    def grade_submission(
        test_id: int,
        student_id: int,
        student_answers: Dict[str, str],  # {"q_1": "B", "q_2": "Photosynthesis is the process..."}
    ) -> StudentSubmission:
        """
        Grades all questions (MCQ + Short answers) and stores the record in SQLite.
        """
        db = SessionLocal()
        try:
            test = db.query(OnlineTest).filter(OnlineTest.id == test_id).first()
            student = db.query(Student).filter(Student.id == student_id).first()
            settings = db.query(AcademySettings).first()

            if not test or not student:
                raise ValueError("Invalid test_id or student_id")

            mcq_marks = 0.0
            short_marks = 0.0
            total_possible_marks = sum(q.marks for q in test.questions)
            feedback_items = []

            for q in test.questions:
                ans_key = f"q_{q.id}"
                user_ans = student_answers.get(ans_key, "").strip()

                if q.question_type == "mcq":
                    # Clean comparison: e.g. 'A' or 'Option A'
                    correct = (q.correct_answer or "").strip().upper()
                    given = user_ans.strip().upper()
                    
                    if correct in given or given in correct:
                        mcq_marks += q.marks
                        feedback_items.append(f"Q{q.id} (MCQ): Correct (+{q.marks} marks)")
                    else:
                        feedback_items.append(f"Q{q.id} (MCQ): Incorrect (Selected: {given}, Correct: {correct})")

                elif q.question_type == "short":
                    # Grade written short answer
                    awarded, note = AIGradingService._grade_short_question(
                        question_text=q.question_text,
                        expected_answer=q.correct_answer or "",
                        student_answer=user_ans,
                        max_marks=q.marks,
                        gemini_key=settings.gemini_api_key if settings else "",
                    )
                    short_marks += awarded
                    feedback_items.append(f"Q{q.id} (Short): {awarded}/{q.marks} marks. {note}")

            total_obtained = round(mcq_marks + short_marks, 2)
            percentage = round((total_obtained / total_possible_marks * 100.0) if total_possible_marks > 0 else 0.0, 2)
            grade_letter = compute_grade_letter(percentage)

            ai_feedback = "\n".join(feedback_items)

            submission = StudentSubmission(
                test_id=test.id,
                student_id=student.id,
                answers_json=json.dumps(student_answers),
                mcq_marks=mcq_marks,
                short_marks=short_marks,
                total_obtained=total_obtained,
                percentage=percentage,
                grade=grade_letter,
                ai_feedback=ai_feedback,
                status="Graded",
            )
            db.add(submission)
            db.commit()
            db.refresh(submission)
            return submission

        finally:
            db.close()

    @staticmethod
    def _grade_short_question(
        question_text: str,
        expected_answer: str,
        student_answer: str,
        max_marks: float,
        gemini_key: str = "",
    ) -> tuple[float, str]:
        """
        Grades short response using Gemini if key is provided,
        or uses conceptual keyword-overlap semantic analysis fallback.
        """
        if not student_answer.strip():
            return 0.0, "No answer provided."

        # 1. Try Gemini AI if API key is saved
        if gemini_key:
            try:
                from google import genai
                client = genai.Client(api_key=gemini_key)
                prompt = (
                    f"You are a strict yet encouraging teacher.\n"
                    f"Question: {question_text}\n"
                    f"Model Expected Answer: {expected_answer}\n"
                    f"Student's Answer: {student_answer}\n"
                    f"Maximum Marks: {max_marks}\n\n"
                    f"Respond ONLY with a valid JSON in this exact structure:\n"
                    f'{{"marks": <number between 0 and {max_marks}>, "comment": "<one short feedback sentence>"}}'
                )
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                )
                txt = response.text.strip()
                # Extract JSON
                json_match = re.search(r"\{.*\}", txt, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(0))
                    marks = min(max_marks, max(0.0, float(data.get("marks", 0.0))))
                    comment = data.get("comment", "Evaluated by AI.")
                    return marks, comment
            except Exception:
                pass  # Fall through to semantic heuristic

        # 2. Intelligent Semantic Heuristic Evaluator (Offline)
        exp_words = set(re.findall(r"\w+", expected_answer.lower()))
        stud_words = set(re.findall(r"\w+", student_answer.lower()))
        
        # Stopwords filter
        stopwords = {"the", "is", "at", "which", "on", "a", "an", "and", "or", "to", "in", "of", "it", "for", "with", "as"}
        exp_keywords = exp_words - stopwords
        
        if not exp_keywords:
            awarded = round(max_marks * 0.75, 1) if len(stud_words) >= 4 else 0.0
            return awarded, "Good effort."

        matched = exp_keywords.intersection(stud_words)
        ratio = len(matched) / len(exp_keywords)

        # Scale marks based on concept coverage & length
        if ratio >= 0.7:
            awarded = max_marks
            remark = "Excellent explanation with all key concepts covered."
        elif ratio >= 0.45:
            awarded = round(max_marks * 0.8, 1)
            remark = "Good answer covering primary principles."
        elif ratio >= 0.2:
            awarded = round(max_marks * 0.5, 1)
            remark = "Partially correct; missed some core terminology."
        else:
            awarded = round(max_marks * 0.25, 1) if len(stud_words) > 5 else 0.0
            remark = "Needs revision; concept was not adequately explained."

        return awarded, remark
