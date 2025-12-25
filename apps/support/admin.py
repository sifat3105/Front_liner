from django.urls import reverse
from django.contrib import admin
from django.utils.html import format_html
from .models import SupportTicket

try:
    from unfold.admin import UnfoldModelAdmin
    UnfoldBase = UnfoldModelAdmin
except Exception:
    UnfoldBase = admin.ModelAdmin

@admin.register(SupportTicket)
class SupportTicketAdmin(UnfoldBase):
    list_display = ("id", "name", "created_by_link", "status_badge", "created_at", "updated_at")
    list_filter = ("status", "created_at")
    search_fields = ("name", "email", "issue_description", "created_by__email")
    readonly_fields = ("created_at", "updated_at")

    actions = ["mark_resolved"]

    def created_by_link(self, obj):
        if obj.created_by:
            return format_html('<a href="{}">{}</a>', reverse("admin:users_user_change", args=(obj.created_by.pk,)), obj.created_by.email)
        return "-"
    created_by_link.short_description = "Created By"

    def status_badge(self, obj):
        colors = {"open": "#f59e0b", "in_progress": "#3b82f6", "resolved": "#16a34a", "closed": "#6b7280"}
        color = colors.get(obj.status, "#6b7280")
        return format_html('<span style="background:{};color:#fff;padding:2px 6px;border-radius:6px;">{}</span>', color, obj.get_status_display())
    status_badge.short_description = "Status"

    def mark_resolved(self, request, queryset):
        updated = queryset.update(status="resolved")
        self.message_user(request, f"{updated} ticket(s) marked resolved.")
    mark_resolved.short_description = "Mark selected tickets as Resolved"
