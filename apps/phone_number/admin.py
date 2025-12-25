from django.urls import reverse
from django.contrib import admin
from django.utils.html import format_html
from .models import PhoneNumber

try:
    from unfold.admin import ModelAdmin
    UnfoldBase = ModelAdmin
except Exception:
    UnfoldBase = admin.ModelAdmin

@admin.register(PhoneNumber)
class PhoneNumberAdmin(UnfoldBase):
    list_display = ("phone_number_link", "user_link", "verified_badge", "price", "created_at")
    list_display_links = ("phone_number_link",)
    search_fields = ("phone_number", "user__email", "number_sid")
    list_filter = ("verified", "created_at")
    list_select_related = ["user"]
    ordering = ["-created_at"]
    list_per_page = 20
    date_hierarchy = "created_at"

    readonly_fields = ("created_at", "updated_at", "number_sid")

    fieldsets = (
        ("Phone Number Info", {
            "fields": ("user", "friendly_name", "phone_number", "number_sid", "verified", "price"),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    @admin.display(description="Phone Number")
    def phone_number_link(self, obj):
        # Link to the change page of this PhoneNumber
        url = reverse("admin:phone_number_phonenumber_change", args=(obj.id,))
        return format_html('<a href="{}">{}</a>', url, obj.phone_number)

    @admin.display(description="User", ordering="user__email")
    def user_link(self, obj):
        if obj.user:
            url = reverse("admin:users_user_change", args=(obj.user.pk,))
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return "-"

    @admin.display(description="Verified")
    def verified_badge(self, obj):
        color = "#16a34a" if obj.verified else "#6b7280"
        text = "Verified" if obj.verified else "Unverified"
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 6px;border-radius:6px;">{}</span>',
            color, text
        )
