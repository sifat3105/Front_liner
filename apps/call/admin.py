from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from .models import CallLog, CallCampaign

@admin.register(CallLog)
class CallLogAdmin(ModelAdmin):
    list_display = (
        "call_sid",
        "call_status_badge",
        "call_duration",
        "caller",
        "callee",
        "timestamp",
        "cost",
        "recording_link",
        "created_at",
    )
    search_fields = ("assistant__name", "call_sid", "caller", "callee", "record_sid")
    list_filter = ("call_status", "assistant")
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ["assistant"]
    list_per_page = 25
    date_hierarchy = "created_at"

    fieldsets = (
        ("Call Info", {
            "fields": (
                "assistant",
                "call_sid",
                "record_sid",
                "call_status",
                "call_duration",
                "caller",
                "callee",
                "timestamp",
                "cost",
                "recording_url",
            )
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    # ==============================
    # Custom Display Methods
    # ==============================
   

    def call_status_badge(self, obj):
        color_map = {
            "completed": "#16a34a",
            "in-progress": "#facc15",
            "failed": "#dc2626",
            "ringing": "#3b82f6",
        }
        color = color_map.get(obj.call_status.lower(), "#6b7280")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 6px;border-radius:6px;">{}</span>',
            color,
            obj.call_status
        )
    call_status_badge.short_description = "Status"

    def recording_link(self, obj):
        if obj.recording_url:
            return format_html('<a href="{}" target="_blank">Recording</a>', obj.recording_url)
        return "-"
    recording_link.short_description = "Recording"


admin.site.register(CallCampaign)