"""
views/test_view.py
------------------
Tab 3: Online Test & Auto-Grading Suite.
Features:
- Create Online Tests with MCQs and Short Questions.
- Add MCQs with 4 options and model answers for short questions.
- Generate unique student test links for WhatsApp dispatch.
- 1-Click "Send Quiz Link to Student" button.
"""

import webbrowser
import urllib.parse
import flet as ft
from services.test_service import TestService
from services.student_service import StudentService
from services.whatsapp_service import WhatsAppService, clean_phone


def create_test_view(page: ft.Page) -> ft.Control:
    """Builds the Online Test & Auto-Grading Suite Tab."""

    tests_list_column = ft.Column(spacing=12, scroll=ft.ScrollMode.ADAPTIVE, expand=True)

    def show_toast(msg: str, is_error: bool = False):
        sb = ft.SnackBar(
            content=ft.Text(msg, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.RED_700 if is_error else ft.Colors.GREEN_700,
        )
        page.overlay.append(sb)
        sb.open = True
        page.update()

    def send_quiz_link_to_student(test, student):
        quiz_url = TestService.generate_quiz_url(test.id, student.id)
        msg = WhatsAppService.build_quiz_invite_message(student, test, quiz_url)
        cl = clean_phone(student.student_phone)
        if not cl:
            show_toast("Student phone number missing.", is_error=True)
            return
        url = f"https://wa.me/{cl}?text={urllib.parse.quote(msg)}"
        webbrowser.open(url)
        show_toast(f"Opening WhatsApp invite for {student.name}...")

    def open_dispatch_student_picker(test):
        students = StudentService.list_students(grade=test.grade)
        if not students:
            show_toast(f"No students registered in {test.grade}.", is_error=True)
            return

        student_buttons = []
        for s in students:
            student_buttons.append(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.PERSON, color=ft.Colors.BLUE_400),
                    title=ft.Text(s.name, weight=ft.FontWeight.BOLD),
                    subtitle=ft.Text(f"{s.roll_number} • {s.student_phone}", size=11, color=ft.Colors.GREY_400),
                    trailing=ft.FilledButton(
                        "Send Link",
                        on_click=lambda e, st=s, t=test: (page.pop_dialog(), send_quiz_link_to_student(t, st)),
                        style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700),
                    ),
                )
            )

        dlg = ft.AlertDialog(
            title=ft.Text(f"Dispatch Test ({test.grade})", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(f"Select student to send '{test.title}' WhatsApp link:", size=12, color=ft.Colors.GREY_300),
                        ft.Column(controls=student_buttons, spacing=4, scroll=ft.ScrollMode.ADAPTIVE),
                    ],
                    spacing=8,
                ),
                width=340,
                height=350,
            ),
            actions=[ft.TextButton("Close", on_click=lambda e: page.pop_dialog())],
        )
        page.show_dialog(dlg)

    def open_add_question_dialog(test):
        q_type_dd = ft.Dropdown(
            label="Question Type",
            value="mcq",
            options=[ft.dropdown.Option("mcq", "Multiple Choice (MCQ)"), ft.dropdown.Option("short", "Written Short Question")],
        )
        q_text = ft.TextField(label="Question Statement", multiline=True, min_lines=2)
        opt_a = ft.TextField(label="Option A")
        opt_b = ft.TextField(label="Option B")
        opt_c = ft.TextField(label="Option C")
        opt_d = ft.TextField(label="Option D")
        correct_ans = ft.TextField(label="Correct Answer (e.g. 'B' or model answer)")
        marks_field = ft.TextField(label="Marks", value="5", keyboard_type=ft.KeyboardType.NUMBER)

        mcq_fields_container = ft.Column(controls=[opt_a, opt_b, opt_c, opt_d], spacing=6)

        def on_type_change(e):
            mcq_fields_container.visible = (q_type_dd.value == "mcq")
            correct_ans.label = "Correct Option (A, B, C, or D)" if q_type_dd.value == "mcq" else "Model Answer / Rubric"
            page.update()

        q_type_dd.on_change = on_type_change

        def save_question(e):
            if not q_text.value or not correct_ans.value:
                show_toast("Question statement and correct answer required.", is_error=True)
                return
            try:
                m_val = float(marks_field.value) if marks_field.value else 5.0
                TestService.add_question(
                    test_id=test.id,
                    question_type=q_type_dd.value,
                    question_text=q_text.value,
                    marks=m_val,
                    option_a=opt_a.value if q_type_dd.value == "mcq" else None,
                    option_b=opt_b.value if q_type_dd.value == "mcq" else None,
                    option_c=opt_c.value if q_type_dd.value == "mcq" else None,
                    option_d=opt_d.value if q_type_dd.value == "mcq" else None,
                    correct_answer=correct_ans.value,
                )
                page.pop_dialog()
                show_toast(f"Added {q_type_dd.value.upper()} question to {test.title}!")
                refresh_tests()
            except Exception as ex:
                show_toast(f"Error: {ex}", is_error=True)

        dlg = ft.AlertDialog(
            title=ft.Text(f"Add Question to {test.title}", weight=ft.FontWeight.BOLD, size=16),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        q_type_dd,
                        q_text,
                        mcq_fields_container,
                        correct_ans,
                        marks_field,
                    ],
                    spacing=8,
                    scroll=ft.ScrollMode.ADAPTIVE,
                ),
                width=340,
                height=380,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog()),
                ft.FilledButton("Save Question", on_click=save_question),
            ],
        )
        page.show_dialog(dlg)

    def refresh_tests():
        tests_list_column.controls.clear()
        tests = TestService.list_tests()

        if not tests:
            tests_list_column.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.QUIZ_OUTLINED, size=50, color=ft.Colors.GREY_600),
                            ft.Text("No online tests created yet.", color=ft.Colors.GREY_400),
                            ft.Text("Tap '+ Create Test' to generate an online exam link.", size=12, color=ft.Colors.GREY_500),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    alignment=ft.alignment.center,
                    padding=30,
                )
            )
            page.update()
            return

        for t in tests:
            q_count = len(t.questions)
            card = ft.Container(
                content=ft.Column(
                    controls=[
                        # Header
                        ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Text(t.grade, size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_200),
                                    bgcolor=ft.Colors.BLUE_900,
                                    padding=ft.padding.symmetric(horizontal=8, vertical=3),
                                    border_radius=6,
                                ),
                                ft.Container(
                                    content=ft.Text(f"{q_count} Questions", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_200),
                                    bgcolor=ft.Colors.INDIGO_900,
                                    padding=ft.padding.symmetric(horizontal=8, vertical=3),
                                    border_radius=6,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        # Title
                        ft.Text(t.title, size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.Text(f"Subject: {t.subject} • Duration: {t.duration_minutes}m • Total: {t.total_marks} Marks", size=12, color=ft.Colors.GREY_400),
                        ft.Divider(height=1, color=ft.Colors.GREY_800),
                        # Action Row
                        ft.Row(
                            controls=[
                                ft.OutlinedButton(
                                    content=ft.Row([ft.Icon(ft.Icons.ADD, size=14), ft.Text("Add Question", size=11)]),
                                    on_click=lambda e, test_obj=t: open_add_question_dialog(test_obj),
                                ),
                                ft.FilledButton(
                                    content=ft.Row([ft.Icon(ft.Icons.SEND, size=14), ft.Text("Send to WA", size=11)]),
                                    bgcolor=ft.Colors.GREEN_700,
                                    on_click=lambda e, test_obj=t: open_dispatch_student_picker(test_obj),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.END,
                            spacing=6,
                        ),
                    ],
                    spacing=8,
                ),
                bgcolor=ft.Colors.GREY_900,
                border_radius=14,
                padding=12,
                border=ft.border.all(1, ft.Colors.GREY_800),
            )
            tests_list_column.controls.append(card)

        page.update()

    # Create Test Dialog
    t_title = ft.TextField(label="Test Title", hint_text="e.g. Chapter 1 Unit Exam")
    t_grade = ft.Dropdown(
        label="Class / Grade",
        value="10th",
        options=[
            ft.dropdown.Option("9th"),
            ft.dropdown.Option("10th"),
            ft.dropdown.Option("1st Year"),
            ft.dropdown.Option("2nd Year"),
        ],
    )
    t_subject = ft.Dropdown(
        label="Subject",
        value="Mathematics",
        options=[
            ft.dropdown.Option("Science"),
            ft.dropdown.Option("Mathematics"),
            ft.dropdown.Option("English"),
            ft.dropdown.Option("Computer Science"),
        ],
    )
    t_duration = ft.TextField(label="Duration (Minutes)", value="30", keyboard_type=ft.KeyboardType.NUMBER)
    t_marks = ft.TextField(label="Total Marks", value="50", keyboard_type=ft.KeyboardType.NUMBER)

    def save_new_test(e):
        if not t_title.value:
            show_toast("Test title is required.", is_error=True)
            return
        try:
            dur = int(t_duration.value) if t_duration.value else 30
            tot = float(t_marks.value) if t_marks.value else 50.0
            new_t = TestService.create_test(
                title=t_title.value,
                grade=t_grade.value,
                subject=t_subject.value,
                duration_minutes=dur,
                total_marks=tot,
            )
            page.pop_dialog()
            t_title.value = ""
            show_toast(f"Test '{new_t.title}' created! Now tap 'Add Question'.")
            refresh_tests()
        except Exception as ex:
            show_toast(f"Error: {ex}", is_error=True)

    def open_create_test_dialog(e):
        dlg = ft.AlertDialog(
            title=ft.Text("Create New Online Test", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(
                    controls=[t_title, t_grade, t_subject, t_duration, t_marks],
                    spacing=10,
                ),
                width=340,
                height=320,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog()),
                ft.FilledButton("Create Test", on_click=save_new_test),
            ],
        )
        page.show_dialog(dlg)

    # Initial load
    refresh_tests()

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("Online Assessments", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.FilledButton(
                            content=ft.Row([ft.Icon(ft.Icons.ADD, size=16), ft.Text("New Test", size=13)]),
                            on_click=open_create_test_dialog,
                            style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=12, vertical=6)),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.INFO_OUTLINE, size=16, color=ft.Colors.BLUE_300),
                            ft.Text("Students open quiz link in WhatsApp without installing any app.", size=11, color=ft.Colors.BLUE_200, expand=True),
                        ],
                        spacing=8,
                    ),
                    bgcolor=ft.Colors.BLUE_950,
                    padding=10,
                    border_radius=8,
                    border=ft.border.all(1, ft.Colors.BLUE_800),
                ),
                tests_list_column,
            ],
            spacing=14,
            expand=True,
        ),
        padding=12,
        expand=True,
    )
