from django.contrib import admin
from .models import Vendor, VendorInvoice, VendorPayment
from django.db.models import Sum
from django.utils.html import format_html

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



class VendorPaymentInline(admin.TabularInline):
    model = VendorPayment
    extra = 1

@admin.register(VendorInvoice)
class VendorInvoiceAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'vendor',
        'invoice_number',
        'invoice_date',
        'invoice_amount',
        'total_payment',
        'due_amount',
        'status_badge',
    )

    list_filter = (
        'invoice_date',
        'vendor',
    )

    search_fields = (
        'invoice_number',
        'vendor__shop_name',
    )

    ordering = ('-invoice_date',)

    inlines = [VendorPaymentInline]

    def total_payment(self, obj):
        return obj.payments.aggregate(
            total=Sum('payment_amount')
        )['total'] or 0
    total_payment.short_description = "Payment"

    def due_amount(self, obj):
        return obj.invoice_amount - self.total_payment(obj)
    due_amount.short_description = "Due"

    def status_badge(self, obj):
        paid = self.total_payment(obj)
        due = obj.invoice_amount - paid

        if due == 0:
            return format_html('<b style="color:green;">PAID</b>')
        elif paid > 0:
            return format_html('<b style="color:orange;">PARTIAL</b>')
        return format_html('<b style="color:red;">DUE</b>')

    status_badge.short_description = "Status"