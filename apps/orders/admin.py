from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from .models import Order, OrderCallConfirmation, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    fields = ("product_name", "product_image", "quantity", "color", "size", "weight", "notes")
    readonly_fields = ()
    show_change_link = True

@admin.register(Order)
class OrderAdmin(UnfoldModelAdmin):
    list_display = (
        "order_id",
        "customer",
        "location",
        "contact",
        "order_amount",
        "platform",
        "status",
        "order_status",
        "user",
    )
    list_filter = ("status", "order_status", "platform")
    search_fields = ("order_id", "customer", "contact", "location")
    readonly_fields = ("order_id",)
    ordering = ("-id",)
    inlines = [OrderItemInline]

    def view_link(self, obj):
        return f'<a href="{obj.get_view_action()}">View</a>'
    view_link.allow_tags = True
    view_link.short_description = "Action"


@admin.register(OrderCallConfirmation)
class OrderCallConfirmationAdmin(UnfoldModelAdmin):
    list_display = (
        "order",
        "status",
        "call_sid",
        "from_number",
        "to_number",
        "courier_booking_ref",
        "confirmed_by",
        "confirmed_at",
    )
    list_filter = ("status",)
    search_fields = ("order__order_id", "call_sid", "to_number", "from_number")
    readonly_fields = ("created_at", "updated_at")
