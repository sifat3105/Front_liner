from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from .models import CallLog, CallCampaign

# =========================
# Call Log
# =========================
@admin.register(CallLog)
class CallLogAdmin(UnfoldModelAdmin):
    list_display = (
        "id", "assistant", "call_sid", "call_status",
        "call_duration", "direction", "caller", "callee", "cost", "timestamp", "created_at"
    )
    list_filter = ("call_status", "direction", "assistant")
    search_fields = ("call_sid", "caller", "callee", "assistant__name")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

    fieldsets = (
        ("Basic Info", {
            "fields": ("assistant", "call_sid", "record_sid", "call_status", "call_duration", "direction")
        }),
        ("Participants", {
            "fields": ("caller", "callee", "timestamp")
        }),
        ("Recording & Cost", {
            "fields": ("recording_url", "cost")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at")
        }),
    )


# =========================
# Call Campaign
# =========================
@admin.register(CallCampaign)
class CallCampaignAdmin(UnfoldModelAdmin):
    list_display = (
        "id", "serial_number", "phone_number", "name", "designation", "company", "business_type"
    )
    search_fields = ("serial_number", "phone_number", "name", "company")
    readonly_fields = ("serial_number",)  # generated automatically
    ordering = ("id",)

    fieldsets = (
        ("Basic Info", {
            "fields": ("name", "designation", "company", "business_type")
        }),
        ("Phone", {
            "fields": ("phone_number", "serial_number")
        }),
    )
