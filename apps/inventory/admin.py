from django.contrib import admin
from .models import Product,ProductItem,ProductPurchase, ProductPurchaseItem


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "product",
        "image",
        "vendor",
        # "brand",
        "price",
        "status",
    )
    list_filter = ("status", "vendor")
    search_fields = ("product", "brand")


class ProductPurchaseItemInline(admin.TabularInline):
    model = ProductPurchaseItem
    extra = 1


@admin.register(ProductPurchase)
class ProductPurchaseAdmin(admin.ModelAdmin):
    list_display = ("id", "vendor", "order_date")
    inlines = [ProductPurchaseItemInline]
