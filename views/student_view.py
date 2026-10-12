
"""
views/student_view.py
Student Directory for Academy Management App
"""

import webbrowser
import flet as ft

from services.student_service import StudentService
from services.whatsapp_service import clean_phone


def create_student_view(page: ft.Page) -> ft.Control:
    selected_grade = "All Classes"
    search_query = ""

    students_list_column = ft.Column(
        spacing=12,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    def show_toast(msg: str, is_error: bool = False):
        sb = ft.SnackBar(
            content=ft.Text(msg, color=ft.Colors.WHITE),
            bgcolor=(
                ft.Colors.RED_700
                if is_error
                else ft.Colors.GREEN_700
            ),
        )
        page.overlay.append(sb)
        sb.open = True
        page.update()

    def open_whatsapp(
        phone: str,
        student_name: str,
        is_parent: bool = False,
    ):
        cl = clean_phone(phone or "")

        if not cl:
            show_toast(
                "Phone number is missing or invalid.",
                is_error=True,
            )
            return

        from urllib.parse import quote

        greeting = (
            "Assalam-o-Alaikum! Regarding student "
            f"{student_name} from THE LAHORE ACADAMY JHANG."
        )

        url = f"https://wa.me/{cl}?text={quote(greeting)}"
        webbrowser.open(url)

        recipient = "Parent" if is_parent else "Student"
        show_toast(f"Opening WhatsApp chat with {recipient}...")

    def refresh_students():
        students_list_column.controls.clear()

        try:
            students = StudentService.list_students(
                grade=selected_grade,
                search=search_query,
            )
        except Exception as ex:
            students_list_column.controls.append(
                ft.Text(
                    f"Unable to load students: {ex}",
                    color=ft.Colors.RED_400,
                )
            )
            page.update()
            return

        if not students:
            students_list_column.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(
                                ft.Icons.PEOPLE_OUTLINE,
                                size=50,
                                color=ft.Colors.GREY_600,
                            ),
                            ft.Text(
                                "No students found",
                                size=16,
                                color=ft.Colors.GREY_400,
                                weight=ft.FontWeight.W_500,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    alignment=ft.Alignment.CENTER,
                    padding=40,
                )
            )
            page.update()
            return

        for s in students:
            is_paid = s.fee_status == "Paid"

            status_color = (
                ft.Colors.GREEN_400
                if is_paid
                else ft.Colors.RED_400
            )
            status_bg = (
                ft.Colors.GREEN_900
                if is_paid
                else ft.Colors.RED_900
            )

            student_name = s.name or "Student"
            student_initial = (
                student_name[0].upper()
                if student_name
                else "S"
            )

            card = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Text(
                                        str(s.roll_number or "N/A"),
                                        size=11,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.BLUE_200,
                                    ),
                                    bgcolor=ft.Colors.BLUE_900,
                                    padding=ft.Padding(
                                        left=8,
                                        top=3,
                                        right=8,
                                        bottom=3,
                                    ),
                                    border_radius=6,
                                ),
                                ft.Container(
                                    content=ft.Text(
                                        str(s.fee_status or "Unpaid"),
                                        size=11,
                                        weight=ft.FontWeight.BOLD,
                                        color=status_color,
                                    ),
                                    bgcolor=status_bg,
                                    padding=ft.Padding(
                                        left=8,
                                        top=3,
                                        right=8,
                                        bottom=3,
                                    ),
                                    border_radius=6,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Row(
                            controls=[
                                ft.CircleAvatar(
                                    content=ft.Text(
                                        student_initial,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                    bgcolor=ft.Colors.INDIGO_700,
                                    radius=22,
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            student_name,
                                            size=16,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.WHITE,
                                        ),
                                        ft.Text(
                                            f"{s.grade} • Fee: PKR "
                                            f"{float(s.monthly_fee or 0):,.0f}",
                                            size=12,
                                            color=ft.Colors.GREY_400,
                                        ),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Text(
                            f"Father: {s.parent_name or 'N/A'} "
                            f"({s.parent_phone or 'N/A'})",
                            size=12,
                            color=ft.Colors.GREY_300,
                        ),
                        ft.Divider(
                            height=1,
                            color=ft.Colors.GREY_800,
                        ),
                        ft.Row(
                            controls=[
                                ft.OutlinedButton(
                                    content=ft.Row(
                                        controls=[
                                            ft.Icon(
                                                ft.Icons.CHAT,
                                                size=14,
                                                color=ft.Colors.GREEN_400,
                                            ),
                                            ft.Text(
                                                "Student WA",
                                                size=12,
                                                color=ft.Colors.GREEN_400,
                                            ),
                                        ],
                                        spacing=4,
                                    ),
                                    on_click=lambda e, ph=s.student_phone, n=student_name: (
                                        open_whatsapp(ph, n)
                                    ),
                                ),
                                ft.FilledButton(
                                    content=ft.Row(
                                        controls=[
                                            ft.Icon(
                                                ft.Icons.CHAT,
                                                size=14,
                                                color=ft.Colors.WHITE,
                                            ),
                                            ft.Text(
                                                "Parent WA",
                                                size=12,
                                                color=ft.Colors.WHITE,
                                            ),
                                        ],
                                        spacing=4,
                                    ),
                                    bgcolor=ft.Colors.GREEN_700,
                                    on_click=lambda e, ph=s.parent_phone, n=student_name: (
                                        open_whatsapp(ph, n, True)
                                    ),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.END,
                            spacing=8,
                            wrap=True,
                        ),
                    ],
                    spacing=8,
                ),
                bgcolor=ft.Colors.GREY_900,
                border_radius=14,
                padding=14,
                border=ft.Border.all(
                    1,
                    ft.Colors.GREY_800,
                ),
            )

            students_list_column.controls.append(card)

        page.update()

    # Student registration fields
    name_field = ft.TextField(
        label="Student Full Name",
        hint_text="e.g. Ali Khan",
    )

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

    parent_name_field = ft.TextField(
        label="Father / Guardian Name",
        hint_text="e.g. Tariq Khan",
    )

    parent_phone_field = ft.TextField(
        label="Parent WhatsApp Number",
        hint_text="03001234567",
    )

    student_phone_field = ft.TextField(
        label="Student Phone Number",
        hint_text="03007654321",
    )

    fee_field = ft.TextField(
        label="Monthly Fee (PKR)",
        value="5000",
        keyboard_type=ft.KeyboardType.NUMBER,
    )

    def close_dialog():
        page.pop_dialog()

    def save_new_student(e):
        if (
            not (name_field.value or "").strip()
            or not (parent_name_field.value or "").strip()
            or not (parent_phone_field.value or "").strip()
        ):
            show_toast(
                "Please fill all required student details.",
                is_error=True,
            )
            return

        try:
            fee_val = float(fee_field.value or "5000")

            StudentService.create_student(
                name=name_field.value.strip(),
                grade=grade_dropdown.value or "9th",
                student_phone=(
                    student_phone_field.value or ""
                ).strip() or parent_phone_field.value.strip(),
                parent_name=parent_name_field.value.strip(),
                parent_phone=parent_phone_field.value.strip(),
                monthly_fee=fee_val,
            )

            close_dialog()

            name_field.value = ""
            parent_name_field.value = ""
            parent_phone_field.value = ""
            student_phone_field.value = ""
            fee_field.value = "5000"

            show_toast("Student successfully enrolled!")
            refresh_students()

        except ValueError:
            show_toast(
                "Please enter a valid monthly fee.",
                is_error=True,
            )
        except Exception as ex:
            show_toast(f"Error: {ex}", is_error=True)

    def open_add_dialog(e):
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                "Register New Student",
                weight=ft.FontWeight.BOLD,
            ),
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
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=340,
                height=380,
            ),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=lambda e: close_dialog(),
                ),
                ft.FilledButton(
                    "Save Student",
                    on_click=save_new_student,
                ),
            ],
        )

        page.show_dialog(dlg)

    # Search and filter handlers
    def on_grade_filter_change(e):
        nonlocal selected_grade
        selected_grade = e.control.value or "All Classes"
        refresh_students()

    def on_search_change(e):
        nonlocal search_query
        search_query = e.control.value or ""
        refresh_students()

    search_box = ft.TextField(
        prefix_icon=ft.Icons.SEARCH,
        hint_text="Search student by name or roll #...",
        on_change=on_search_change,
        expand=True,
        dense=True,
    )

    # IMPORTANT:
    # The filter dropdown uses on_change, supported by standard Flet.
    # If your runtime rejects this argument, check the installed Flet
    # version and runtime compatibility rather than removing the handler.
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
        width=150,
        dense=True,
    )

    refresh_students()

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(
                            "Student Directory",
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                        ),
                        ft.FilledButton(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(
                                        ft.Icons.PERSON_ADD,
                                        size=16,
                                    ),
                                    ft.Text("Add", size=13),
                                ],
                            ),
                            on_click=open_add_dialog,
                            style=ft.ButtonStyle(
                                padding=ft.Padding(
                                    left=12,
                                    top=6,
                                    right=12,
                                    bottom=6,
                                )
                            ),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Row(
                    controls=[
                        search_box,
                        filter_dropdown,
                    ],
                    spacing=8,
                ),
                students_list_column,
            ],
            spacing=14,
            expand=True,
        ),
        padding=12,
        expand=True,
    )
