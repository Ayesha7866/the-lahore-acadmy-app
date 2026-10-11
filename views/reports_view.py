"""
views/reports_view.py
---------------------
Tab 4: Reports & WhatsApp Dispatcher.
Features:
- View student test submissions with auto-computed percentages & grades.
- 1-Click "Send Scorecard to Father" via WhatsApp.
- QR-Code WhatsApp Pairing status card.
"""

import webbrowser
import urllib.parse
import flet as ft
from services.test_service import TestService
from services.fee_service import FeeService
from services.whatsapp_service import WhatsAppService, clean_phone


def create_reports_view(page: ft.Page) -> ft.Control:
    """Builds the Reports & WhatsApp Dispatcher Tab."""

    submissions_list_column = ft.Column(spacing=12, scroll=ft.ScrollMode.ADAPTIVE, expand=True)

    def show_toast(msg: str, is_error: bool = False):
        sb = ft.SnackBar(
            content=ft.Text(msg, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.RED_700 if is_error else ft.Colors.GREEN_700,
        )
        page.overlay.append(sb)
        sb.open = True
        page.update()

    def send_scorecard_to_parent(sub):
        settings = FeeService.get_settings()
        msg = WhatsAppService.build_test_scorecard_message(sub, settings=settings)
        phone = sub.student.parent_phone
        cl = clean_phone(phone)
        if not cl:
            show_toast("Parent phone number missing.", is_error=True)
            return

        url = f"https://wa.me/{cl}?text={urllib.parse.quote(msg)}"
        webbrowser.open(url)
        show_toast(f"Opening WhatsApp scorecard for {sub.student.parent_name}...")

    def show_feedback_dialog(sub):
        dlg = ft.AlertDialog(
            title=ft.Text(f"AI Evaluation - {sub.student.name}", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(f"Test: {sub.test.title} ({sub.test.subject})", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_300),
                        ft.Text(f"Score: {sub.total_obtained}/{sub.test.total_marks} ({sub.percentage}%) - Grade {sub.grade}", size=12, color=ft.Colors.WHITE),
                        ft.Divider(height=1, color=ft.Colors.GREY_700),
                        ft.Text("Detailed Breakdown:", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_400),
                        ft.Text(sub.ai_feedback or "No detailed breakdown available.", size=12, color=ft.Colors.GREY_200),
                    ],
                    spacing=8,
                    scroll=ft.ScrollMode.ADAPTIVE,
                ),
                width=340,
                height=300,
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda e: page.pop_dialog()),
                ft.FilledButton("Send to Parent WA", on_click=lambda e, s=sub: (page.pop_dialog(), send_scorecard_to_parent(s))),
            ],
        )
        page.show_dialog(dlg)

    def refresh_submissions():
        submissions_list_column.controls.clear()
        subs = TestService.list_submissions()

        if not subs:
            submissions_list_column.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.ASSESSMENT_OUTLINED, size=50, color=ft.Colors.GREY_600),
                            ft.Text("No online exam submissions yet.", color=ft.Colors.GREY_400),
                            ft.Text("When students submit tests via WhatsApp links, results appear here.", size=11, color=ft.Colors.GREY_500),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    alignment=ft.alignment.center,
                    padding=30,
                )
            )
            page.update()
            return

        for s in subs:
            grade_color = ft.Colors.GREEN_400 if s.grade in ["A+", "A"] else ft.Colors.BLUE_400 if s.grade == "B" else ft.Colors.ORANGE_400 if s.grade in ["C", "D"] else ft.Colors.RED_400

            card = ft.Container(
                content=ft.Column(
                    controls=[
                        # Header
                        ft.Row(
                            controls=[
                                ft.Column(
                                    controls=[
                                        ft.Text(s.student.name, size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                        ft.Text(f"{s.student.grade} • {s.test.subject}", size=11, color=ft.Colors.GREY_400),
                                    ],
                                    spacing=2,
                                ),
                                ft.Container(
                                    content=ft.Text(f"Grade {s.grade}", size=12, weight=ft.FontWeight.BOLD, color=grade_color),
                                    bgcolor=ft.Colors.GREY_800,
                                    padding=ft.padding.symmetric(horizontal=10, vertical=4),
                                    border_radius=8,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        # Test details & Score
                        ft.Row(
                            controls=[
                                ft.Text(s.test.title, size=12, color=ft.Colors.GREY_300, expand=True),
                                ft.Text(f"{s.total_obtained}/{s.test.total_marks} ({s.percentage}%)", size=13, weight=ft.FontWeight.BOLD, color=grade_color),
                            ],
                        ),
                        ft.Divider(height=1, color=ft.Colors.GREY_800),
                        # Action Row
                        ft.Row(
                            controls=[
                                ft.OutlinedButton(
                                    content=ft.Row([ft.Icon(ft.Icons.VISIBILITY, size=14), ft.Text("AI Feedback", size=11)]),
                                    on_click=lambda e, sub_obj=s: show_feedback_dialog(sub_obj),
                                ),
                                ft.FilledButton(
                                    content=ft.Row([ft.Icon(ft.Icons.CHAT, size=14), ft.Text("Send to Father", size=11)]),
                                    bgcolor=ft.Colors.GREEN_700,
                                    on_click=lambda e, sub_obj=s: send_scorecard_to_parent(sub_obj),
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
            submissions_list_column.controls.append(card)

        page.update()

    # QR WhatsApp Engine Info Dialog
    def open_qr_engine_dialog(e):
        dlg = ft.AlertDialog(
            title=ft.Text("WhatsApp Pairing Engine", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Container(
                            content=ft.Icon(ft.Icons.QR_CODE_2, size=90, color=ft.Colors.GREEN_400),
                            alignment=ft.alignment.center,
                        ),
                        ft.Text("Direct Mobile WhatsApp Integration Active", weight=ft.FontWeight.BOLD, size=13, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER),
                        ft.Text("• Zero Meta Cloud API fees\n• Sends messages directly from your WhatsApp\n• Tap any student or parent button to open WhatsApp instantly with the full message pre-filled.", size=11, color=ft.Colors.GREY_300),
                    ],
                    spacing=10,
                ),
                width=320,
                height=260,
            ),
            actions=[ft.FilledButton("Got It", on_click=lambda e: page.pop_dialog())],
        )
        page.show_dialog(dlg)

    # Initial load
    refresh_submissions()

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("Reports & Dispatches", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.IconButton(
                            icon=ft.Icons.QR_CODE,
                            tooltip="WhatsApp Engine Status",
                            on_click=open_qr_engine_dialog,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                # WhatsApp Pairing Banner
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.CHECK_CIRCLE, size=18, color=ft.Colors.GREEN_400),
                            ft.Column(
                                controls=[
                                    ft.Text("WhatsApp Engine: Direct Mobile Mode", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                    ft.Text("1-Tap instant dispatch to parents • 100% Free", size=10, color=ft.Colors.GREY_400),
                                ],
                                spacing=1,
                                expand=True,
                            ),
                            ft.OutlinedButton("Status", on_click=open_qr_engine_dialog, style=ft.ButtonStyle(padding=ft.padding.all(6))),
                        ],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    bgcolor=ft.Colors.GREEN_950,
                    padding=10,
                    border_radius=10,
                    border=ft.border.all(1, ft.Colors.GREEN_800),
                ),
                # List of Submissions
                submissions_list_column,
            ],
            spacing=12,
            expand=True,
        ),
        padding=12,
        expand=True,
    )
