
"""
main.py
-------
Academy Management & WhatsApp Automation Mobile App
Flet Framework
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

    # Initialize Database
    init_db()
    seed_mobile_database()

    # Start Quiz Web Server
    try:
        start_quiz_server_thread(
            host="0.0.0.0",
            port=8000,
        )
    except Exception as e:
        print(f"Quiz server warning: {e}")

    # Load Academy Settings
    settings = FeeService.get_settings()

    # App Bar
    page.app_bar = ft.AppBar(
        leading=ft.Icon(
            ft.Icons.SCHOOL,
            color=ft.Colors.BLUE_400,
        ),
        title=ft.Text(
            settings.academy_name or "THE LAHORE ACADAMY JHANG",
            size=16,
            weight=ft.FontWeight.BOLD,
        ),
        bgcolor=ft.Colors.GREY_900,
        center_title=False,
    )

    # Main Content Area
    content_area = ft.Container(expand=True)

    # Load Selected Tab
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

    # Navigation Change Handler
    def on_nav_change(e):
        load_tab(e.control.selected_index)

    # Bottom Navigation Bar
    page.navigation_bar = ft.NavigationBar(
        selected_index=0,
        on_change=on_nav_change,
        bgcolor=ft.Colors.GREY_900,
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

    # Initial View
    load_tab(0)

    # Add Content
    page.add(content_area)


if __name__ == "__main__":
    if hasattr(ft, "run"):
        ft.run(main)
    elif hasattr(ft, "app"):
        ft.app(target=main)
