from django.contrib import admin
from .models import (
    Income,
    Payments,
    CustomerRefund,
    VoucherType,
    VoucherEntry,
    ProfitLossReport,
    Receiver,Product,
    Invoice, Payment
)


# Income section admin
@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'owner',
        'total_income',
        'monthly_income',
        'daily_income',
        'created_at',
    )
    list_filter = ('owner', 'created_at')
    search_fields = ('owner__username',)
    ordering = ('-created_at',)

@admin.register(Payments)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'owner',
        'customer',
        'amount',
        'payment_method',
        'status',
        'date',
        'created_at',
    )
    list_filter = ('status', 'payment_method', 'date', 'owner')
    search_fields = ('customer', 'owner__username')
    ordering = ('-date',)


# Refund section admin
@admin.register(CustomerRefund)
class CustomerRefundAdmin(admin.ModelAdmin):

    # Admin list page
    list_display = (
        'id',
        'owner',
        'location',
        'contact',
        'price',
        'platform',
        'refund_status',
    )

    # Right side filter
    list_filter = (
        'refund_status',
        'platform',
        'owner',
    )

    #  search box 
    search_fields = (
        'location',
        'contact',
        'owner__username',
    )

    # Latest data 
    ordering = ('-id',)

    # Admin panel edit options
    readonly_fields = ('id',)

    # New refund order create & owner auto assign
    def save_model(self, request, obj, form, change):
        if not obj.owner:
            obj.owner = request.user
        super().save_model(request, obj, form, change)


# Voucher Type Admin
@admin.register(VoucherType)
class VoucherTypeAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'name',
        'is_active',
    )

    list_filter = ('is_active',)

    search_fields = ('name',)

    ordering = ('name',)

    readonly_fields = ('id',)


# Voucher Entry Admin
@admin.register(VoucherEntry)
class VoucherEntryAdmin(admin.ModelAdmin):
    """
    Admin configuration for VoucherEntry (Accounting Vouchers)
    """

    list_display = (
        'id',
        'voucher_no',
        'voucher_date',
        'customer_name',
        'voucher_type',
        'nature',
        'amount',
        'status',
        'posted',
    )

    list_filter = (
        'status',
        'posted',
        'nature',
        'voucher_type',
    )

    search_fields = (
        'voucher_no',
        'customer_name',
    )

    ordering = ('-id',)

    readonly_fields = (
        'id',
        'created_at',
    )

    # Auto assign owner from admin panel
    def save_model(self, request, obj, form, change):
        if not obj.owner:
            obj.owner = request.user
        super().save_model(request, obj, form, change)


# Profit & Loss (P&L) section
@admin.register(ProfitLossReport)
class ProfitLossReportAdmin(admin.ModelAdmin):
    """
    Admin dashboard for Profit & Loss Reports
    """

    # Columns to display in admin list view
    list_display = (
        'date',
        'revenue',
        'expenses',
        'operating_expenses',
        'gross_profit',
        'net_profit',
        'status',
        'owner',
    )

    # Filters in sidebar
    list_filter = (
        'status',
        'date',
    )

    # Search by date
    search_fields = (
        'date',
    )

    # Order by latest date first
    ordering = ('-date',)

    # Fields that are read-only in admin (cannot edit manually)
    readonly_fields = (
        'gross_profit',
        'net_profit',
        'created_at',
    )

    # Auto assign owner when creating in admin panel
    def save_model(self, request, obj, form, change):
        if not obj.owner:
            obj.owner = request.user
        super().save_model(request, obj, form, change)


# Payment section

# Receiver Admin
@admin.register(Receiver)
class ReceiverAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'receiver_type')
    search_fields = ('name', 'receiver_type')
    list_filter = ('receiver_type',)


# Product Admin
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description')
    search_fields = ('name',)
    list_filter = ('name',)


# Invoice Admin
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'invoice_number', 'receiver', 'created_at')
    search_fields = ('invoice_number', 'receiver__name')
    list_filter = ('receiver__receiver_type',)
    readonly_fields = ('created_at',)


# Payment Admin
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'receiver',
        'product',
        'invoice',
        'description',
        'quantity',
        'amount',
        'payment_method',
        'cheque_number',
        'created_at'
    )
    search_fields = ('receiver__name', 'invoice__invoice_number', 'product__name')
    list_filter = ('payment_method', 'receiver__receiver_type')
    readonly_fields = ('created_at',)
