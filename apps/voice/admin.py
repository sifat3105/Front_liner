from django.urls import reverse
from django.contrib import admin
from django.utils.html import format_html
from .models import Agent

try:
    from unfold.admin import UnfoldModelAdmin
    UnfoldBase = UnfoldModelAdmin
except Exception:
    UnfoldBase = admin.ModelAdmin

@admin.register(Agent)
class AgentAdmin(UnfoldBase):
    list_display = ("name", "owner_link", "enabled_badge", "language", "voice", "created_at")
    list_filter = ("enabled", "language", "voice", "created_at")
    search_fields = ("name", "owner__email")
    readonly_fields = ("public_id", "created_at", "updated_at")

    fieldsets = (
        ("Basics", {"fields": ("owner", "name", "welcome_message")}),
        ("Behavior", {"fields": ("agent_prompt", "business_details", "voice", "language", "enabled")}),
        ("Meta", {"fields": ("public_id", "theme_primary", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def owner_link(self, obj):
        if obj.owner:
            return format_html('<a href="{}">{}</a>', reverse("admin:users_user_change", args=(obj.owner.pk,)), obj.owner.email)
        return "-"
    owner_link.short_description = "Owner"

    def enabled_badge(self, obj):
        color = "#16a34a" if obj.enabled else "#ef4444"
        text = "Enabled" if obj.enabled else "Disabled"
        return format_html('<span style="background:{};color:#fff;padding:2px 6px;border-radius:6px;">{}</span>', color, text)
    enabled_badge.short_description = "Status"
