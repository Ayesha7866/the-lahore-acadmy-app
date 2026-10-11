"""
main.py
-------
Academy Management & WhatsApp Automation Mobile App (Flet Framework)
Designed for Academy Admin/Owner:
- Client Communication: 100% Free direct WhatsApp dispatch via mobile deep-links & Web QR session.
- Student Online Tests: Web exam links sent to students via WhatsApp with zero app install needed.
- Auto-Grading: Instant MCQs + Google Gemini AI short answer evaluation.
- Payment Gateways: Embedded JazzCash, EasyPaisa, and Bank details in fee reminders.
- Packaging: Ready for 'flet build apk' Android compilation.
"""

import threading
import flet as ft

from database import init_db
from seed_data import seed_mobile_database
from services.quiz_server import start_quiz_server_thread
from services.fee_service import FeeService

from views.student_view import create_student_view
from views.fee_view import create_fee_view
from views.test_view import create_test_view
from views.reports_view import create_reports_view


def main(page: ft.Page):
    # Mobile Portrait Configuration
    page.title = "THE LAHORE ACADAMY JHANG"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0

    # Initialize Database & Seed demo data if first run
    init_db()
    seed_mobile_database()

    # Start Quiz Web Server daemon in background so students can take tests via WhatsApp links
    try:
        start_quiz_server_thread(host="0.0.0.0", port=8000)
    except Exception as e:
        print(f"Quiz server warning: {e}")

    # App Bar (Header at top of screen)
    settings = FeeService.get_settings()
    page.app_bar = ft.AppBar(
        leading=ft.Icon(ft.Icons.SCHOOL, color=ft.Colors.BLUE_400),
        title=ft.Text(settings.academy_name or "THE LAHORE ACADAMY JHANG", size=16, weight=ft.FontWeight.BOLD),
        bgcolor=ft.Colors.GREY_950,
        center_title=False,
    )

    # Views dictionary for bottom navigation
    content_area = ft.Container(expand=True)

    def load_tab(index: int):
        if index == 0:
            content_area.content = create_student_view(page)
        elif index == 1:
            content_area.content = create_fee_view(page)
        elif index == 2:
            content_area.content = create_test_view(page)
        elif index == 3:
            content_area.content = create_reports_view(page)
        page.update()

    def on_nav_change(e):
        load_tab(e.control.selected_index)

    # Bottom Navigation Bar (Material 3 Native Mobile Navigation)
    page.navigation_bar = ft.NavigationBar(
        selected_index=0,
        on_change=on_nav_change,
        bgcolor=ft.Colors.GREY_950,
        destinations=[
            ft.NavigationBarDestination(
                icon=ft.Icons.PEOPLE_OUTLINE,
                selected_icon=ft.Icons.PEOPLE,
                label="Students",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.PAYMENTS_OUTLINED,
                selected_icon=ft.Icons.PAYMENTS,
                label="Fees",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.QUIZ_OUTLINED,
                selected_icon=ft.Icons.QUIZ,
                label="Online Tests",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.ASSESSMENT_OUTLINED,
                selected_icon=ft.Icons.ASSESSMENT,
                label="Reports",
            ),
        ],
    )

    # Initial view load
    load_tab(0)
    page.add(content_area)


if __name__ == "__main__":
    if hasattr(ft, "run"):
        ft.run(main)
    elif hasattr(ft, "app"):
        ft.app(target=main)
