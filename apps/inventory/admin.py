from django.contrib import admin
from .models import Order, Size, Color,ProductPurchase, ProductPurchaseItem


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code')
    search_fields = ('name',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "product",
        "vendor",
        "brand",
        "price",
        "status",
        "created",
    )
    list_filter = ("status", "brand", "vendor")
    search_fields = ("product", "brand")
    filter_horizontal = ("sizes", "colors")


class ProductPurchaseItemInline(admin.TabularInline):
    model = ProductPurchaseItem
    extra = 1


@admin.register(ProductPurchase)
class ProductPurchaseAdmin(admin.ModelAdmin):
    list_display = ("id", "vendor", "order_date")
    inlines = [ProductPurchaseItemInline]
