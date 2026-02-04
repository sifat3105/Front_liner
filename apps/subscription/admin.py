import re

from django import forms
from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin

from .models import SubscriptionPermission, SubscriptionPlan, UserSubscription


def _default_permission_name(code: str) -> str:
    return code.replace("-", " ").replace("_", " ").title()


def _parse_permission_codes(raw_value: str):
    items = re.split(r"[\n,]+", raw_value or "")
    result = []
    seen = set()
    for item in items:
        code = (item or "").strip().lower()
        if not code:
            continue
        if not re.fullmatch(r"[a-z0-9_-]+", code):
            raise forms.ValidationError(
                f"Invalid permission code '{code}'. Use only a-z, 0-9, _ or -."
            )
        if code in seen:
            continue
        seen.add(code)
        result.append(code)
    return result


class SubscriptionPlanAdminForm(forms.ModelForm):
    permissions_input = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 6,
                "class": "permissions-chip-input",
                "placeholder": "chat_use\nvoice_call\nanalytics_dashboard",
            }
        ),
        help_text="Type code then press Enter/comma. Codes appear as tags in the same input.",
        label="Permissions",
    )

    class Meta:
        model = SubscriptionPlan
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            codes = self.instance.permissions.order_by("code").values_list("code", flat=True)
            self.fields["permissions_input"].initial = "\n".join(codes)

    def clean_permissions_input(self):
        return _parse_permission_codes(self.cleaned_data.get("permissions_input"))

    class Media:
        css = {
            "all": ("subscription/admin_permissions_tags.css",),
        }
        js = ("subscription/admin_permissions_tags.js",)


@admin.register(SubscriptionPermission)
class SubscriptionPermissionAdmin(UnfoldModelAdmin):
    list_display = ("id", "plan", "code", "name", "is_active", "created_at")
    list_filter = ("is_active", "plan")
    search_fields = ("code", "name", "plan__name")
    ordering = ("plan", "name", "id")
    readonly_fields = ("created_at",)
    list_select_related = ("plan",)


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(UnfoldModelAdmin):
    form = SubscriptionPlanAdminForm
    list_display = (
        "id",
        "name",
        "price",
        "interval",
        "interval_count",
        "is_active",
        "permission_count",
        "created_at",
    )
    list_filter = ("is_active", "interval")
    search_fields = ("name",)
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)
    fields = (
        "name",
        "price",
        "interval",
        "interval_count",
        "is_active",
        "features",
        "permissions_input",
        "created_at",
    )

    def permission_count(self, obj):
        return obj.permissions.count()

    permission_count.short_description = "Permissions"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        codes = form.cleaned_data.get("permissions_input", [])
        if codes is None:
            return

        for code in codes:
            permission, created = SubscriptionPermission.objects.get_or_create(
                plan=obj,
                code=code,
                defaults={
                    "name": _default_permission_name(code),
                    "description": "",
                    "is_active": True,
                },
            )
            if not created and not permission.is_active:
                permission.is_active = True
                permission.save(update_fields=["is_active"])

        obj.permissions.exclude(code__in=codes).delete()


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
