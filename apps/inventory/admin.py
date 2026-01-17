from django.contrib import admin
from .models import Product,ProductItem


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "product",
        "image",
        "vendor",
        "price",
        "status",
    )
    list_filter = ("status", "vendor")
    search_fields = ("product", "brand")

