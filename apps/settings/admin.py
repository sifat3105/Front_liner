from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.decorators import display
from django.utils.html import format_html
from .models import AgentPricePerMonth, MinimumTopup, CallCostPerMinute

# --- Agent Price Per Month ---
@admin.register(AgentPricePerMonth)
class AgentPricePerMonthAdmin(ModelAdmin):
    # Use actual model field for inline editing
    list_display = ["price"]
    list_editable = ["price"]
    list_display_links = None  # remove links to enable inline editing

    fieldsets = (
        ("Agent Pricing Settings", {
            "fields": ("price",),
            "classes": ("collapse open",),
        }),
    )

    def has_add_permission(self, request, obj=None):
        # Allow adding only if no instance exists
        return not AgentPricePerMonth.objects.exists()

    def has_change_permission(self, request, obj=None):
        return True


# --- Minimum Topup ---
@admin.register(MinimumTopup)
class MinimumTopupAdmin(ModelAdmin):
    list_display = ["amount"]
    list_editable = ["amount"]
    list_display_links = None

    fieldsets = (
        ("Top-up Settings", {
            "fields": ("amount",),
            "classes": ("collapse open",),
        }),
    )

    def has_add_permission(self, request, obj=None):
        return not MinimumTopup.objects.exists()

    def has_change_permission(self, request, obj=None):
        return True


# --- Call Cost Per Minute ---
@admin.register(CallCostPerMinute)
class CallCostPerMinuteAdmin(ModelAdmin):
    list_display = ["price"]
    list_editable = ["price"]
    list_display_links = None

    fieldsets = (
        ("Call Cost Settings", {
            "fields": ("price",),
            "classes": ("collapse open",),
        }),
    )

    def has_add_permission(self, request, obj=None):
        return not CallCostPerMinute.objects.exists()

    def has_change_permission(self, request, obj=None):
        return True
