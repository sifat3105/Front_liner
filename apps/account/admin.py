from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin

from .models import (
    Income, Payments, Sells, Refund,
    DebitCredit, ProfitLossReport,
    Receiver, Product, Invoice, Payment
)

# =========================
# Income
# =========================
@admin.register(Income)
class IncomeAdmin(UnfoldModelAdmin):
    list_display = (
        "id", "owner", "customer",
        "amount", "payment_method",
        "date"
    )
    list_filter = ("payment_method", "date")
    search_fields = ("customer", "owner__username")
    ordering = ("-date",)
    readonly_fields = ("created_at",)


# =========================
# Payments (Customer)
# =========================
@admin.register(Payments)
class PaymentsAdmin(UnfoldModelAdmin):
    list_display = (
        "id", "owner", "customer",
        "amount", "payment_method",
        "status", "date"
    )
    list_filter = ("status", "payment_method", "date")
    search_fields = ("customer", "owner__username")
    ordering = ("-date",)
    readonly_fields = ("created_at", "updated_at")


# =========================
# Sells
# =========================
@admin.register(Sells)
class SellsAdmin(UnfoldModelAdmin):
    list_display = (
        "id", "order_id", "owner",
        "customer", "order_amount",
        "platform", "sells_status"
    )
    list_filter = ("platform", "sells_status")
    search_fields = ("order_id", "customer", "contact")
    ordering = ("-id",)


# =========================
# Refund
# =========================
@admin.register(Refund)
class RefundAdmin(UnfoldModelAdmin):
    list_display = (
        "id", "order_id", "owner",
        "customer", "order_amount",
        "platform", "refund_status"
    )
    list_filter = ("platform", "refund_status")
    search_fields = ("order_id", "customer", "contact")
    ordering = ("-id",)


# =========================
# Debit / Credit Ledger
# =========================
@admin.register(DebitCredit)
class DebitCreditAdmin(UnfoldModelAdmin):
    list_display = (
        "id", "owner", "customer_name",
        "payment_type", "amount",
        "debit", "credit",
        "balance", "created_at"
    )
    list_filter = ("payment_type", "created_at")
    search_fields = ("customer_name", "voucher_no", "invoice_no")
    ordering = ("created_at",)
    readonly_fields = (
        "debit", "credit",
        "balance", "created_at"
    )


# =========================
# Profit & Loss Report
# =========================
@admin.register(ProfitLossReport)
class ProfitLossReportAdmin(UnfoldModelAdmin):
    list_display = (
        "id", "owner", "date",
        "revenue", "expenses",
        "gross_profit", "net_profit"
    )
    list_filter = ("date",)
    search_fields = ("owner__username",)
    ordering = ("-date",)
    readonly_fields = ("created_at",)


# =========================
# Receiver
# =========================
@admin.register(Receiver)
class ReceiverAdmin(UnfoldModelAdmin):
    list_display = ("id", "name", "receiver_type")
    list_filter = ("receiver_type",)
    search_fields = ("name",)


# =========================
# Product
# =========================
@admin.register(Product)
class ProductAdmin(UnfoldModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


# =========================
# Invoice
# =========================
@admin.register(Invoice)
class InvoiceAdmin(UnfoldModelAdmin):
    list_display = (
        "id", "invoice_number",
        "receiver", "created_at"
    )
    search_fields = (
        "invoice_number",
        "receiver__name"
    )
    readonly_fields = ("created_at",)


# =========================
# Payment
# =========================
@admin.register(Payment)
class PaymentAdmin(UnfoldModelAdmin):
    list_display = (
        "id", "receiver",
        "product", "quantity",
        "amount", "payment_method",
        "created_at"
    )
    list_filter = ("payment_method", "created_at")
    search_fields = (
        "receiver__name",
        "product__name"
    )
    readonly_fields = ("created_at",)
