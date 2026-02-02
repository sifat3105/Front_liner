from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin

from .models import SubscriptionPlan, UserSubscription


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(UnfoldModelAdmin):
    list_display = (
        "id",
        "name",
        "price",
        "interval",
        "interval_count",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "interval")
    search_fields = ("name",)
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)


@admin.register(UserSubscription)
class UserSubscriptionAdmin(UnfoldModelAdmin):
    list_display = (
        "id",
        "user",
        "plan",
        "status",
        "started_at",
        "expires_at",
        "last_renewed_at",
        "is_active_now",
    )
    list_filter = ("status", "plan")
    search_fields = ("user__email", "plan__name")
    ordering = ("-id",)
    list_select_related = ("user", "plan")

    def is_active_now(self, obj):
        return obj.is_active()

    is_active_now.boolean = True
    is_active_now.short_description = "Active Now"
