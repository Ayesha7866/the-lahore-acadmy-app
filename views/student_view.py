"""
views/student_view.py
---------------------
Tab 1: Student Directory view for the Academy Mobile App.
Displays student cards, filters by class, searches, and provides
direct 1-tap WhatsApp chat buttons to students and parents.
"""

import webbrowser
import flet as ft
from services.student_service import StudentService
from services.whatsapp_service import clean_phone


def create_student_view(page: ft.Page) -> ft.Control:
    """Builds the Student Directory Tab."""

    # UI State
    selected_grade = "All Classes"
    search_query = ""

    # Controls
    students_list_column = ft.Column(spacing=12, scroll=ft.ScrollMode.ADAPTIVE, expand=True)

    def show_toast(msg: str, is_error: bool = False):
        sb = ft.SnackBar(
            content=ft.Text(msg, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.RED_700 if is_error else ft.Colors.GREEN_700,
        )
        page.overlay.append(sb)
        sb.open = True
        page.update()

    def open_whatsapp(phone: str, student_name: str, is_parent: bool = False):
        cl = clean_phone(phone)
        if not cl:
            show_toast("Phone number is missing or invalid.", is_error=True)
            return
        greeting = f"Assalam-o-Alaikum! Regarding student {student_name} from THE LAHORE ACADAMY JHANG."
        url = f"https://wa.me/{cl}?text={greeting}"
        webbrowser.open(url)
        show_toast(f"Opening WhatsApp chat with {'Parent' if is_parent else 'Student'}...")

    def refresh_students():
        students_list_column.controls.clear()
        students = StudentService.list_students(grade=selected_grade, search=search_query)

        if not students:
            students_list_column.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.PEOPLE_OUTLINE, size=50, color=ft.Colors.GREY_600),
                            ft.Text("No students found", size=16, color=ft.Colors.GREY_400, weight=ft.FontWeight.W_500),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    alignment=ft.alignment.center,
                    padding=40,
                )
            )
            page.update()
            return

        for s in students:
            is_paid = s.fee_status == "Paid"
            status_color = ft.Colors.GREEN_400 if is_paid else ft.Colors.RED_400
            status_bg = ft.Colors.GREEN_900 if is_paid else ft.Colors.RED_900

            card = ft.Container(
                content=ft.Column(
                    controls=[
                        # Header: Roll No & Fee Badge
                        ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Text(s.roll_number, size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_200),
                                    bgcolor=ft.Colors.BLUE_900,
                                    padding=ft.padding.symmetric(horizontal=8, vertical=3),
                                    border_radius=6,
                                ),
                                ft.Container(
                                    content=ft.Text(s.fee_status, size=11, weight=ft.FontWeight.BOLD, color=status_color),
                                    bgcolor=status_bg,
                                    padding=ft.padding.symmetric(horizontal=8, vertical=3),
                                    border_radius=6,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        # Student Info
                        ft.Row(
                            controls=[
                                ft.CircleAvatar(
                                    content=ft.Text(s.name[0].upper(), weight=ft.FontWeight.BOLD),
                                    bgcolor=ft.Colors.INDIGO_700,
                                    radius=22,
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(s.name, size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                        ft.Text(f"{s.grade} • Fee: PKR {s.monthly_fee:,.0f}", size=12, color=ft.Colors.GREY_400),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        # Parent details
                        ft.Text(f"Father: {s.parent_name} ({s.parent_phone})", size=12, color=ft.Colors.GREY_300),
                        # Action Buttons
                        ft.Divider(height=1, color=ft.Colors.GREY_800),
                        ft.Row(
                            controls=[
                                ft.OutlinedButton(
                                    content=ft.Row(
                                        controls=[
                                            ft.Icon(ft.Icons.CHAT, size=14, color=ft.Colors.GREEN_400),
                                            ft.Text("Student WA", size=12, color=ft.Colors.GREEN_400),
                                        ],
                                        spacing=4,
                                    ),
                                    on_click=lambda e, ph=s.student_phone, n=s.name: open_whatsapp(ph, n, is_parent=False),
                                ),
                                ft.FilledButton(
                                    content=ft.Row(
                                        controls=[
                                            ft.Icon(ft.Icons.CHAT, size=14, color=ft.Colors.WHITE),
                                            ft.Text("Parent WA", size=12, color=ft.Colors.WHITE),
                                        ],
                                        spacing=4,
                                    ),
                                    bgcolor=ft.Colors.GREEN_700,
                                    on_click=lambda e, ph=s.parent_phone, n=s.name: open_whatsapp(ph, n, is_parent=True),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.END,
                            spacing=8,
                        ),
                    ],
                    spacing=8,
                ),
                bgcolor=ft.Colors.GREY_900,
                border_radius=14,
                padding=14,
                border=ft.border.all(1, ft.Colors.GREY_800),
            )
            students_list_column.controls.append(card)

        page.update()

    # Register Student Dialog
    name_field = ft.TextField(label="Student Full Name", hint_text="e.g. Ali Khan")
    grade_dropdown = ft.Dropdown(
        label="Class / Grade",
        value="9th",
        options=[
            ft.dropdown.Option("9th"),
            ft.dropdown.Option("10th"),
            ft.dropdown.Option("1st Year"),
            ft.dropdown.Option("2nd Year"),
        ],
    )
    parent_name_field = ft.TextField(label="Father / Guardian Name", hint_text="e.g. Tariq Khan")
    parent_phone_field = ft.TextField(label="Parent WhatsApp Number", hint_text="03001234567")
    student_phone_field = ft.TextField(label="Student Phone Number", hint_text="03007654321")
    fee_field = ft.TextField(label="Monthly Fee (PKR)", value="5000", keyboard_type=ft.KeyboardType.NUMBER)

    def save_new_student(e):
        if not name_field.value or not parent_phone_field.value or not parent_name_field.value:
            show_toast("Please fill all required student details.", is_error=True)
            return

        try:
            fee_val = float(fee_field.value) if fee_field.value else 5000.0
            StudentService.create_student(
                name=name_field.value,
                grade=grade_dropdown.value,
                student_phone=student_phone_field.value or parent_phone_field.value,
                parent_name=parent_name_field.value,
                parent_phone=parent_phone_field.value,
                monthly_fee=fee_val,
            )
            page.pop_dialog()
            # Clear fields
            name_field.value = ""
            parent_name_field.value = ""
            parent_phone_field.value = ""
            student_phone_field.value = ""
            show_toast("Student successfully enrolled!")
            refresh_students()
        except Exception as ex:
            show_toast(f"Error: {ex}", is_error=True)

    def open_add_dialog(e):
        dlg = ft.AlertDialog(
            title=ft.Text("Register New Student", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        name_field,
                        grade_dropdown,
                        parent_name_field,
                        parent_phone_field,
                        student_phone_field,
                        fee_field,
                    ],
                    spacing=10,
                    scroll=ft.ScrollMode.ADAPTIVE,
                ),
                width=340,
                height=380,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog()),
                ft.FilledButton("Save Student", on_click=save_new_student),
            ],
        )
        page.show_dialog(dlg)

    # Search & Filter handlers
    def on_grade_filter_change(e):
        nonlocal selected_grade
        selected_grade = e.control.value
        refresh_students()

    def on_search_change(e):
        nonlocal search_query
        search_query = e.control.value
        refresh_students()

    # Search bar & Class filter
    search_box = ft.TextField(
        prefix_icon=ft.Icons.SEARCH,
        hint_text="Search student by name or roll #...",
        on_change=on_search_change,
        expand=True,
        dense=True,
    )

    filter_dropdown = ft.Dropdown(
        value="All Classes",
        options=[
            ft.dropdown.Option("All Classes"),
            ft.dropdown.Option("9th"),
            ft.dropdown.Option("10th"),
            ft.dropdown.Option("1st Year"),
            ft.dropdown.Option("2nd Year"),
        ],
        on_change=on_grade_filter_change,
        width=130,
        dense=True,
    )

    # Initial population
    refresh_students()

    # Layout container
    return ft.Container(
        content=ft.Column(
            controls=[
                # Top Action Row
                ft.Row(
                    controls=[
                        ft.Text("Student Directory", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.FilledButton(
                            content=ft.Row([ft.Icon(ft.Icons.PERSON_ADD, size=16), ft.Text("Add", size=13)]),
                            on_click=open_add_dialog,
                            style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=12, vertical=6)),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                # Search & Filter Row
                ft.Row(controls=[search_box, filter_dropdown], spacing=8),
                # Student Cards Scroll Area
                students_list_column,
            ],
            spacing=14,
            expand=True,
        ),
        padding=12,
        expand=True,
    )
