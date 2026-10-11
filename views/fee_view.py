"""
views/fee_view.py
-----------------
Tab 2: Fee Management & Payment Gateway Settings view.
Features:
- Payment Gateway Configuration (JazzCash, EasyPaisa, Bank Account, Title, IBAN).
- Financial Recovery KPI metrics.
- 1-Click "Send WhatsApp Fee Reminder" with saved payment gateway info appended.
- 1-Click "Mark as Paid" with digital receipt modal and WhatsApp receipt dispatch.
"""

import webbrowser
import urllib.parse
import flet as ft
from services.fee_service import FeeService
from services.whatsapp_service import WhatsAppService, clean_phone


def create_fee_view(page: ft.Page) -> ft.Control:
    """Builds the Fee Management Tab."""

    fee_list_column = ft.Column(spacing=10, scroll=ft.ScrollMode.ADAPTIVE, expand=True)

    # Metric text labels
    total_collected_text = ft.Text("PKR 0", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_400)
    pending_amount_text = ft.Text("PKR 0", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_400)
    recovery_rate_text = ft.Text("0%", size=14, weight=ft.FontWeight.W_500, color=ft.Colors.BLUE_300)

    def show_toast(msg: str, is_error: bool = False):
        sb = ft.SnackBar(
            content=ft.Text(msg, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.RED_700 if is_error else ft.Colors.GREEN_700,
        )
        page.overlay.append(sb)
        sb.open = True
        page.update()

    def send_fee_reminder(rec):
        settings = FeeService.get_settings()
        msg = WhatsAppService.build_fee_reminder_message(rec, settings=settings)
        phone = rec.student.parent_phone
        cl = clean_phone(phone)
        if not cl:
            show_toast("Parent phone number missing.", is_error=True)
            return

        url = f"https://wa.me/{cl}?text={urllib.parse.quote(msg)}"
        webbrowser.open(url)
        show_toast(f"Opening WhatsApp reminder for {rec.student.name}...")

    def show_receipt_dialog(rec):
        settings = FeeService.get_settings()
        dlg = ft.AlertDialog(
            title=ft.Text("Official Fee Receipt", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(settings.academy_name, size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_300),
                        ft.Divider(height=1, color=ft.Colors.GREY_700),
                        ft.Row([ft.Text("Receipt #:", color=ft.Colors.GREY_400), ft.Text(rec.receipt_number or "REC-001", weight=ft.FontWeight.BOLD)]),
                        ft.Row([ft.Text("Student:", color=ft.Colors.GREY_400), ft.Text(f"{rec.student.name} ({rec.student.grade})", weight=ft.FontWeight.BOLD)]),
                        ft.Row([ft.Text("Father:", color=ft.Colors.GREY_400), ft.Text(rec.student.parent_name)]),
                        ft.Row([ft.Text("Month:", color=ft.Colors.GREY_400), ft.Text(rec.month_year)]),
                        ft.Row([ft.Text("Amount Paid:", color=ft.Colors.GREY_400), ft.Text(f"PKR {rec.amount_paid:,.0f}", color=ft.Colors.GREEN_400, weight=ft.FontWeight.BOLD, size=16)]),
                        ft.Row([ft.Text("Payment Date:", color=ft.Colors.GREY_400), ft.Text(rec.payment_date or "Today")]),
                        ft.Container(
                            content=ft.Text("PAID IN FULL", color=ft.Colors.GREEN_300, weight=ft.FontWeight.BOLD, size=12),
                            bgcolor=ft.Colors.GREEN_900,
                            padding=ft.padding.symmetric(horizontal=12, vertical=4),
                            border_radius=6,
                            alignment=ft.alignment.center,
                        ),
                    ],
                    spacing=8,
                ),
                width=320,
                height=280,
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda e: page.pop_dialog()),
                ft.FilledButton(
                    content=ft.Row([ft.Icon(ft.Icons.CHAT, size=14), ft.Text("Send Receipt WA", size=12)]),
                    on_click=lambda e, r=rec: send_receipt_wa(r),
                    bgcolor=ft.Colors.GREEN_700,
                ),
            ],
        )
        page.show_dialog(dlg)

    def send_receipt_wa(rec):
        settings = FeeService.get_settings()
        phone = rec.student.parent_phone
        cl = clean_phone(phone)
        receipt_text = (
            f"🧾 *{settings.academy_name.upper()} - OFFICIAL PAYMENT RECEIPT*\n\n"
            f"Mohtaram Walidain *{rec.student.parent_name} Sahab*,\n"
            f"Aap ki taraf se fee kamyabi ke sath receive ho chuki hai:\n\n"
            f"• *Receipt #:* {rec.receipt_number}\n"
            f"• *Student:* {rec.student.name} ({rec.student.grade})\n"
            f"• *Month:* {rec.month_year}\n"
            f"• *Amount Paid:* PKR {rec.amount_paid:,.0f}\n"
            f"• *Status:* PAID ✓\n"
            f"• *Date:* {rec.payment_date}\n\n"
            f"Regards,\n*{settings.academy_name}*"
        )
        url = f"https://wa.me/{cl}?text={urllib.parse.quote(receipt_text)}"
        webbrowser.open(url)
        page.pop_dialog()
        show_toast("Opening WhatsApp to send payment receipt...")

    def handle_mark_paid(rec):
        updated = FeeService.mark_as_paid(rec.id)
        if updated:
            show_toast(f"Marked as Paid! Receipt: {updated.receipt_number}")
            refresh_fee_view()
            show_receipt_dialog(updated)

    def refresh_fee_view():
        summary = FeeService.get_financial_summary()
        total_collected_text.value = f"PKR {summary['total_collected']:,.0f}"
        pending_amount_text.value = f"PKR {summary['pending_amount']:,.0f}"
        recovery_rate_text.value = f"Recovery: {summary['recovery_rate']}% ({summary['pending_count']} Pending)"

        fee_list_column.controls.clear()
        records = FeeService.list_fee_records()

        if not records:
            fee_list_column.controls.append(
                ft.Container(
                    content=ft.Text("No invoices generated yet. Tap 'Generate Invoices' above.", color=ft.Colors.GREY_400),
                    alignment=ft.alignment.center,
                    padding=30,
                )
            )
            page.update()
            return

        for rec in records:
            is_paid = rec.status == "Paid"
            status_color = ft.Colors.GREEN_400 if is_paid else ft.Colors.RED_400
            status_bg = ft.Colors.GREEN_900 if is_paid else ft.Colors.RED_900
            balance = rec.amount_due - rec.amount_paid

            card = ft.Container(
                content=ft.Column(
                    controls=[
                        # Top Row: Student Name & Status Badge
                        ft.Row(
                            controls=[
                                ft.Column(
                                    controls=[
                                        ft.Text(rec.student.name, size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                        ft.Text(f"{rec.student.grade} • {rec.month_year}", size=11, color=ft.Colors.GREY_400),
                                    ],
                                    spacing=2,
                                ),
                                ft.Container(
                                    content=ft.Text(rec.status, size=11, weight=ft.FontWeight.BOLD, color=status_color),
                                    bgcolor=status_bg,
                                    padding=ft.padding.symmetric(horizontal=8, vertical=3),
                                    border_radius=6,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        # Amount Info
                        ft.Row(
                            controls=[
                                ft.Text(f"Amount Due: PKR {rec.amount_due:,.0f}", size=12, color=ft.Colors.GREY_300),
                                ft.Text(f"Balance: PKR {balance:,.0f}", size=12, weight=ft.FontWeight.BOLD, color=status_color),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Divider(height=1, color=ft.Colors.GREY_800),
                        # Action Buttons
                        ft.Row(
                            controls=[
                                ft.FilledButton(
                                    content=ft.Row([ft.Icon(ft.Icons.NOTIFICATIONS, size=14), ft.Text("Remind WA", size=11)]),
                                    bgcolor=ft.Colors.ORANGE_800,
                                    on_click=lambda e, r=rec: send_fee_reminder(r),
                                    visible=not is_paid,
                                ),
                                ft.FilledButton(
                                    content=ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE, size=14), ft.Text("Mark as Paid", size=11)]),
                                    bgcolor=ft.Colors.GREEN_700,
                                    on_click=lambda e, r=rec: handle_mark_paid(r),
                                    visible=not is_paid,
                                ),
                                ft.OutlinedButton(
                                    content=ft.Row([ft.Icon(ft.Icons.RECEIPT_LONG, size=14), ft.Text("View Receipt", size=11)]),
                                    on_click=lambda e, r=rec: show_receipt_dialog(r),
                                    visible=is_paid,
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
            fee_list_column.controls.append(card)

        page.update()

    # Payment Gateway Settings Dialog
    def open_gateway_settings(e):
        settings = FeeService.get_settings()
        jc_num = ft.TextField(label="JazzCash Mobile Number", value=settings.jazzcash_number)
        jc_title = ft.TextField(label="JazzCash Account Title", value=settings.jazzcash_title)
        ep_num = ft.TextField(label="EasyPaisa Mobile Number", value=settings.easypaisa_number)
        ep_title = ft.TextField(label="EasyPaisa Account Title", value=settings.easypaisa_title)
        bank_name = ft.TextField(label="Bank Name (e.g. Meezan Bank)", value=settings.bank_name)
        bank_title = ft.TextField(label="Bank Account Title", value=settings.bank_account_title)
        bank_iban = ft.TextField(label="IBAN / Account Number", value=settings.bank_iban)

        def save_gateway_settings(ev):
            FeeService.update_settings(
                jazzcash_number=jc_num.value,
                jazzcash_title=jc_title.value,
                easypaisa_number=ep_num.value,
                easypaisa_title=ep_title.value,
                bank_name=bank_name.value,
                bank_account_title=bank_title.value,
                bank_iban=bank_iban.value,
            )
            page.pop_dialog()
            show_toast("Payment gateway details saved! These will appear in WhatsApp reminders.")

        dlg = ft.AlertDialog(
            title=ft.Text("Payment Gateway Settings", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("These details are automatically embedded into all WhatsApp fee reminders:", size=11, color=ft.Colors.GREY_400),
                        jc_num,
                        jc_title,
                        ep_num,
                        ep_title,
                        bank_name,
                        bank_title,
                        bank_iban,
                    ],
                    spacing=10,
                    scroll=ft.ScrollMode.ADAPTIVE,
                ),
                width=340,
                height=380,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog()),
                ft.FilledButton("Save Settings", on_click=save_gateway_settings),
            ],
        )
        page.show_dialog(dlg)

    def generate_invoices_click(e):
        created = FeeService.generate_monthly_invoices()
        show_toast(f"Generated {created} fee invoices for this month!")
        refresh_fee_view()

    # Initial load
    refresh_fee_view()

    # Layout
    return ft.Container(
        content=ft.Column(
            controls=[
                # Header & Action Row
                ft.Row(
                    controls=[
                        ft.Text("Fee Management", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.IconButton(
                            icon=ft.Icons.SETTINGS,
                            tooltip="Payment Gateway Settings",
                            on_click=open_gateway_settings,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                # Financial KPI Card
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Column([ft.Text("Collected", size=11, color=ft.Colors.GREY_400), total_collected_text], spacing=2),
                                    ft.Column([ft.Text("Pending Dues", size=11, color=ft.Colors.GREY_400), pending_amount_text], spacing=2),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_AROUND,
                            ),
                            ft.Row([recovery_rate_text], alignment=ft.MainAxisAlignment.CENTER),
                        ],
                        spacing=6,
                    ),
                    bgcolor=ft.Colors.GREY_900,
                    padding=12,
                    border_radius=12,
                    border=ft.border.all(1, ft.Colors.BLUE_900),
                ),
                # Quick Action Buttons
                ft.Row(
                    controls=[
                        ft.OutlinedButton(
                            content=ft.Row([ft.Icon(ft.Icons.CALENDAR_MONTH, size=15), ft.Text("Generate Month", size=12)]),
                            on_click=generate_invoices_click,
                            expand=True,
                        ),
                        ft.FilledButton(
                            content=ft.Row([ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET, size=15), ft.Text("Gateways", size=12)]),
                            on_click=open_gateway_settings,
                            expand=True,
                        ),
                    ],
                    spacing=8,
                ),
                # Fee Records List
                fee_list_column,
            ],
            spacing=12,
            expand=True,
        ),
        padding=12,
        expand=True,
    )
