from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils.html import format_html

from .models import Transaction

@admin.register(Transaction)
class TransactionAdmin(ModelAdmin):
    list_display = (
        "transaction_id",
        "user",
        "status_badge",
        "category",
        "amount",
        "payment_method",
        "created_at",
    )

    search_fields = (
        "transaction_id",
        "user__username",
        "user__email",
        "description",
    )

    list_filter = (
        "status",
        "category",
        "payment_method",
        "created_at",
    )

    readonly_fields = ("created_at", "updated_at")

    ordering = ("-created_at",)

    def status_badge(self, obj):
        color = {
            "pending": "orange",
            "completed": "green",
            "failed": "red",
        }.get(obj.status, "gray")

        return format_html(
            '<span style="padding:4px 10px; border-radius:6px; background:{}; color:white; font-weight:600;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Status"
