from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from .models import PhoneNumber

@admin.register(PhoneNumber)
class PhoneNumberAdmin(UnfoldModelAdmin):
    list_display = (
        "phone_number",
        "user",
        "friendly_name",
        "verified",
        "price",
        "number_sid",
        "created_at",
        "updated_at",
    )
    list_filter = ("verified", "created_at")
    search_fields = ("phone_number", "user__email", "friendly_name", "number_sid")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)
