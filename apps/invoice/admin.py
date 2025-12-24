from django.contrib import admin
from django import forms
from unfold.admin import ModelAdmin
from unfold.decorators import display
from django.utils.html import format_html
from .models import Invoice, InvoiceItem, AdminInvoice, AdminInvoiceItem

# ------------------------
# Invoice Items Inline
# ------------------------
class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0
    readonly_fields = ["total"]
    can_delete = True

# ------------------------
# Invoice Admin
# ------------------------
@admin.register(Invoice)
class InvoiceAdmin(ModelAdmin):
    list_display = ["id", "customer", "user_email", "total_amount", "status", "created_at", "due_date"]
    list_display_links = ["id", "customer", "user_email",]
    list_filter = ["status", "created_at", "due_date"]
    search_fields = ["customer", "agent", "user__email"]
    ordering = ["-id"]
    list_per_page = 20
    date_hierarchy = "created_at"
    list_select_related = ["user"]

    inlines = [InvoiceItemInline]

    fieldsets = (
        ("Customer & Agent Info", {
            "fields": ("user", "customer", "agent")
        }),
        ("Invoice Details", {
            "fields": ("due_date", "status",'discount',  "total_amount", "notes")
        }),
        ("Attachments", {
            "fields": ("image",),
            "classes": ("collapse",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    readonly_fields = ["created_at", "updated_at"]

    @display(description="User Email", ordering="user__email")
    def user_email(self, obj):
        return obj.user.email

# ------------------------
# AdminInvoice Items Inline
# ------------------------
class AdminInvoiceItemInline(admin.TabularInline):
    model = AdminInvoiceItem
    extra = 0
    readonly_fields = ["total"]
    can_delete = True

# ------------------------
# AdminInvoice Admin
# ------------------------
@admin.register(AdminInvoice)
class AdminInvoiceAdmin(ModelAdmin):
    list_display = ["invoice_number", "assigned_to_email", "created_by_email", "amount", "status", "created_at", "due_date"]
    list_filter = ["status", "created_at", "due_date"]
    search_fields = ["invoice_number", "assigned_to__email", "created_by__email"]
    ordering = ["-created_at"]
    list_per_page = 20
    date_hierarchy = "created_at"
    list_select_related = ["assigned_to", "created_by"]

    inlines = [AdminInvoiceItemInline]

    fieldsets = (
        ("Invoice Creator & Recipient", {
            "fields": ("created_by", "assigned_to")
        }),
        ("Invoice Details", {
            "fields": ("invoice_number", "due_date", "amount", "status", "description", "notes")
        }),
        ("Timestamps", {
            "fields": ("created_at",),
            "classes": ("collapse",)
        }),
    )

    readonly_fields = ["created_at"]

    @display(description="Assigned To", ordering="assigned_to__email")
    def assigned_to_email(self, obj):
        return obj.assigned_to.email if obj.assigned_to else "—"

    @display(description="Created By", ordering="created_by__email")
    def created_by_email(self, obj):
        return obj.created_by.email if obj.created_by else "—"

# ------------------------
# AdminInvoiceItem Admin
# ------------------------
@admin.register(AdminInvoiceItem)
class AdminInvoiceItemAdmin(ModelAdmin):
    list_display = ["description", "invoice_number", "qty", "unit_price", "total"]
    list_filter = ["invoice__created_at"]
    search_fields = ["description", "invoice__invoice_number"]
    ordering = ["-invoice__created_at"]
    list_per_page = 20
    list_select_related = ["invoice"]

    fieldsets = (
        ("Item Details", {
            "fields": ("invoice", "description", "qty", "unit_price")
        }),
        ("Total", {
            "fields": ("total",),
        }),
    )

    readonly_fields = ["total"]

    @display(description="Invoice Number", ordering="invoice__invoice_number")
    def invoice_number(self, obj):
        return obj.invoice.invoice_number
