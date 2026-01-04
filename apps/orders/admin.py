from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from .models import Order, OrderItem

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
