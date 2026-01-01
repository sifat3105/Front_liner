from django.contrib import admin
from django.db.models import Sum
from django.utils.timezone import now
from .models import (
    Income,
    Payments,
    Refund,
    DebitCredit,
    ProfitLossReport,
    Receiver,Product,
    Invoice, Payment,Sells
)


# Income section admin
@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'date',
        'customer',
        'amount',
        'payment_method',
        'owner',
        'created_at',
    )
    list_filter = ('payment_method', 'date')
    search_fields = ('customer',)
    ordering = ('-date',)
    readonly_fields = ('created_at',)

    def save_model(self, request, obj, form, change):
        if not obj.owner:
            obj.owner = request.user
        super().save_model(request, obj, form, change) or 0


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


# Sells section admin
@admin.register(Sells)
class CustomerSellsAdmin(admin.ModelAdmin):

    # Admin list page
    list_display = (
        'id',
        'owner',
        'order_id',
        'customer',
        'location',
        'contact',
        'order_amount',
        'platform',
        'sells_status',
    )

    # Right side filter
    list_filter = (
        'sells_status',
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



# Refund section admin
@admin.register(Refund)
class CustomerRefundAdmin(admin.ModelAdmin):

    # Admin list page
    list_display = (
        'id',
        'owner',
        'order_id',
        'customer',
        'location',
        'contact',
        'order_amount',
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



# Debit Credit section admin

@admin.register(DebitCredit)
class DebitCreditAdmin(admin.ModelAdmin):

    list_display = (
        'voucher_no',
        'customer_name',
        'payment_description',
        'payment_type',
        'debit',
        'credit',
        'amount',
        'balance',
        'created_at',
    )

    readonly_fields = (
        'debit',
        'credit',
        'balance',
        'created_at',
    )

    search_fields = ('voucher_no', 'customer_name')
    list_filter = ('payment_type', 'created_at')


# Profit & Loss (P&L) section
@admin.register(ProfitLossReport)
class ProfitLossReportAdmin(admin.ModelAdmin):


    # Columns to display in admin list view
    list_display = (
        'id',
        'date',
        'revenue',
        'expenses',
        'gross_profit',
        'net_profit',
        'owner',
    )

    # Filters in sidebar
    list_filter = (
        'id',
        'date',
    )

    # Search by date
    search_fields = (
        'id',
        'date',
    )

    # Order by latest date first
    ordering = ('-date',)

    # Fields that are read-only in admin (cannot edit manually)
    readonly_fields = (
        'id',
        'gross_profit',
        'net_profit',
        'created_at',
    )

    # Auto assign owner when creating in admin panel
    def save_model(self, request, obj, form, change):
        if not obj.owner:
            obj.owner = request.user
        super().save_model(request, obj, form, change)



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
