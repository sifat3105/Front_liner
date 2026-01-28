from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Account, Shop,Business,Banking

class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'role', 'is_staff', 'is_superuser')
    search_fields = ('email',)
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('role', 'is_staff', 'is_superuser')}),
        ('Referral', {'fields': ('refer_user', 'parent')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role', 'is_staff', 'is_superuser'),
        }),
    )

admin.site.register(User, UserAdmin)
admin.site.register(Account)

@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ("shop_name", "owner")
    search_fields = ("shop_name", "business_phone")


# Setting > Profile > business Info Admin
@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ("id","business_type","owner","years_in_business","created_at",)
    search_fields = ("business_type","business_registration_number","tax_id_ein",)



@admin.register(Banking)
class BankingAdmin(admin.ModelAdmin):
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

