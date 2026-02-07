from django.contrib import admin
from django import forms
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.mixins import BaseModelAdminMixin
from unfold.forms import UserChangeForm as UnfoldUserChangeForm
from unfold.widgets import (
    UnfoldAdminPasswordInput,
    UnfoldAdminTextInputWidget,
    UnfoldAdminDecimalFieldWidget,
    UnfoldBooleanWidget,
)

from .models import User, Account, Shop, Business, Banking

try:
    from unfold.admin import ModelAdmin as UnfoldModelAdmin
except Exception:  # pragma: no cover - fallback if unfold is unavailable
    UnfoldModelAdmin = admin.ModelAdmin


class AccountInline(admin.StackedInline):
    model = Account
    fk_name = "user"
    can_delete = False
    extra = 0
    show_change_link = True
    fields = (
        "full_name",
        "phone",
        "organization",
        "balance",
        "is_verified",
        "user_str_id",
        "date_joined",
        "last_login",
    )
    readonly_fields = ("date_joined", "last_login")


class UserAdminCreationForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Password",
        widget=UnfoldAdminPasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=UnfoldAdminPasswordInput(attrs={"autocomplete": "new-password"}),
    )

    full_name = forms.CharField(max_length=255, widget=UnfoldAdminTextInputWidget())
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=UnfoldAdminTextInputWidget(),
    )
    organization = forms.CharField(
        max_length=255,
        required=False,
        widget=UnfoldAdminTextInputWidget(),
    )
    balance = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        initial=0,
        widget=UnfoldAdminDecimalFieldWidget(),
    )
    is_verified = forms.BooleanField(
        required=False,
        initial=False,
        widget=UnfoldBooleanWidget(),
    )
    user_str_id = forms.CharField(
        max_length=255,
        required=False,
        widget=UnfoldAdminTextInputWidget(),
    )

    class Meta:
        model = User
        fields = (
            "email",
            "role",
            "parent",
            "refer_user",
            "refer_token",
            "is_active",
            "is_staff",
            "is_superuser",
            "is_admin",
        )

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()
            Account.objects.update_or_create(
                user=user,
                defaults={
                    "full_name": self.cleaned_data.get("full_name", ""),
                    "phone": self.cleaned_data.get("phone", ""),
                    "organization": self.cleaned_data.get("organization", ""),
                    "balance": self.cleaned_data.get("balance") or 0,
                    "is_verified": self.cleaned_data.get("is_verified", False),
                    "user_str_id": self.cleaned_data.get("user_str_id") or None,
                },
            )
        return user


class UserAdminChangeForm(UnfoldUserChangeForm):

    class Meta:
        model = User
        fields = "__all__"


@admin.register(User)
class UserAdmin(BaseModelAdminMixin, BaseUserAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    list_display = (
        "id",
        "email",
        "role",
        "parent",
        "is_active",
        "is_staff",
        "is_superuser",
        "account_full_name",
        "account_phone",
        "account_organization",
    )
    list_filter = ()
    search_fields = (
        "email",
        "account__full_name",
        "account__phone",
        "account__organization",
    )
    ordering = ("-id",)
    list_select_related = ("parent", "account")
    inlines = (AccountInline,)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("role", "parent", "refer_user", "refer_token")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_admin",
                    "groups",
                    "user_permissions",
                )
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "role",
                    "parent",
                    "refer_user",
                    "refer_token",
                    "full_name",
                    "phone",
                    "organization",
                    "balance",
                    "is_verified",
                    "user_str_id",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_admin",
                ),
            },
        ),
    )

    def get_inlines(self, request, obj=None):
        # While creating user, we already collect account fields in add form.
        if obj is None:
            return ()
        return (AccountInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("parent", "account")

    @admin.display(description="Full Name")
    def account_full_name(self, obj):
        account = getattr(obj, "account", None)
        return account.full_name if account else "-"

    @admin.display(description="Phone")
    def account_phone(self, obj):
        account = getattr(obj, "account", None)
        return account.phone if account and account.phone else "-"

    @admin.display(description="Organization")
    def account_organization(self, obj):
        account = getattr(obj, "account", None)
        return account.organization if account and account.organization else "-"


@admin.register(Account)
class AccountAdmin(UnfoldModelAdmin):
    list_display = (
        "id",
        "user",
        "user_email",
        "user_role",
        "full_name",
        "phone",
        "organization",
        "balance",
        "is_verified",
    )
    list_filter = ("is_verified", "user__role")
    search_fields = ("user__email", "full_name", "phone", "organization", "user_str_id")
    list_select_related = ("user",)
    ordering = ("-id",)

    @admin.display(description="Email")
    def user_email(self, obj):
        return obj.user.email

    @admin.display(description="Role")
    def user_role(self, obj):
        return obj.user.role


@admin.register(Shop)
class ShopAdmin(UnfoldModelAdmin):
    list_display = ("shop_name", "owner")
    search_fields = ("shop_name", "business_phone")


# Setting > Profile > business Info Admin
@admin.register(Business)
class BusinessAdmin(UnfoldModelAdmin):
    list_display = ("id","business_type","owner","years_in_business","created_at",)
    search_fields = ("business_type","business_registration_number","tax_id_ein",)



@admin.register(Banking)
class BankingAdmin(UnfoldModelAdmin):
    list_display = (
        "id",
        "bank_name",
        "account_name",
        "account_number",
        "routing_number",
        "owner",
        "created_at",
    )

    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Owner Information", {
            "fields": ("owner",),
        }),
        ("Bank Details", {
            "fields": (
                "bank_name",
                "account_name",
                "account_number",
                "routing_number",
                "swift_bic_code",
            ),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
        }),
    )
