from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(UnfoldModelAdmin):
    list_display = (
        "invoice_number",
        "user",
        "customer_name",
        "customer_phone",
        "amount",
        "status",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("invoice_number", "customer_name", "customer_phone", "trx_id")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
