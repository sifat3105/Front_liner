from django.contrib import admin
from .models import Vendor

# Register your models here.


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'shop_name',
        'business_email',
        'business_phone',
        'business_type',
        'years_in_business',
        'bank_name',
        'is_active',
        'created_at',
    )

    # Click করলে details page যাবে
    list_display_links = ('id', 'shop_name')

    # Search bar
    search_fields = (
        'shop_name',
        'business_email',
        'business_phone',
        'business_registration_number',
        'tax_id',
    )

    # Right side filter
    list_filter = (
        'business_type',
        'is_active',
        'created_at',
    )

    # Read-only fields
    readonly_fields = ('created_at',)

    # Admin form layout (sections)
    fieldsets = (
        ("Owner Information", {
            "fields": ("owner",),
        }),

        ("Shop Information", {
            "fields": (
                "shop_name",
                "shop_description",
                "business_email",
                "business_phone",
                "business_address",
            ),
        }),

        ("Legal Information", {
            "fields": (
                "business_registration_number",
                "tax_id",
                "business_type",
                "years_in_business",
                "website_url",
            ),
        }),

        ("Bank Information", {
            "fields": (
                "bank_name",
                "account_holder_name",
                "account_number",
                "routing_number",
                "swift_bic_code",
            ),
        }),

        ("System Information", {
            "fields": (
                "is_active",
                "created_at",
            ),
        }),
    )

    # Default ordering
    ordering = ('-created_at',)
