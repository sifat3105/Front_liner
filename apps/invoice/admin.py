from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from .models import Invoice, InvoiceItem, AdminInvoice, AdminInvoiceItem

# =========================
# Inline for Invoice Items
# =========================
class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    readonly_fields = ("total",)
    fields = ("description", "qty", "unit_price", "total")


# =========================
# Invoice Admin
# =========================
@admin.register(Invoice)
class InvoiceAdmin(UnfoldModelAdmin):
    list_display = ("id", "customer", "agent", "total_amount", "status", "due_date", "created_at")
    list_filter = ("status", "due_date")
    search_fields = ("customer", "agent")
    readonly_fields = ("created_at", "updated_at")
    inlines = [InvoiceItemInline]
    ordering = ("-created_at",)


# =========================
# Inline for AdminInvoice Items
# =========================
class AdminInvoiceItemInline(admin.TabularInline):
    model = AdminInvoiceItem
    extra = 1
    readonly_fields = ("total",)
    fields = ("description", "qty", "unit_price", "total")


# =========================
# AdminInvoice Admin
# =========================
@admin.register(AdminInvoice)
class AdminInvoiceAdmin(UnfoldModelAdmin):
    list_display = ("invoice_number", "assigned_to", "created_by", "amount", "status", "invoice_date", "due_date")
    list_filter = ("status", "invoice_date", "due_date")
    search_fields = ("invoice_number", "assigned_to__username", "created_by__username")
    readonly_fields = ("created_at",)
    inlines = [AdminInvoiceItemInline]
    ordering = ("-invoice_date",)
