# from django.contrib import admin
# from unfold.admin import ModelAdmin as UnfoldModelAdmin
# from .models import Product, ProductItem, ProductPurchase, ProductPurchaseItem, Stock, StockItem

# class ProductItemInline(admin.TabularInline):
#     model = ProductItem
#     readonly_fields = ('sku', 'barcode', 'qr_code') 

# @admin.register(Product)
# class ProductAdmin(UnfoldModelAdmin):
#     list_display = ('product', 'vendor', 'status', 'price', 'sale_price', 'quantity', 'created')
#     search_fields = ('product', 'sku', 'vendor__shop_name')
#     list_filter = ('status', 'vendor', 'created')
#     fieldsets = (
#         ('Basic Info', {
#             'fields': ('product', 'vendor', 'brand', 'price', 'sale_price', 'quantity', 'status', )
#         }),
#         ('SKU', {
#             'fields': ('sku', 'barcode', 'qr_code')
#         }),
#     )
#     inlines = [ProductItemInline]
#     readonly_fields = ('sku',)
    
    


# class ProductPurchaseItemInline(admin.TabularInline):
#     model = ProductPurchaseItem
#     extra = 0


# @admin.register(ProductPurchase)
# class ProductPurchaseAdmin(admin.ModelAdmin):
#     list_display = ("id", "vendor", "order_date")
#     inlines = [ProductPurchaseItemInline]


# @admin.register(Stock)
# class StockAdmin(UnfoldModelAdmin):
#     list_display = ("id", "product", "opening", "purchase", "customer_return", "sales", "supplier_return", "damage", "balance", "amount")
#     search_fields = ("product__product", "product__sku")
#     list_filter = ("product", "opening", "purchase", "customer_return", "sales", "supplier_return", "damage")
#     readonly_fields = ("balance", "amount")
    
# @admin.register(StockItem)
# class StockItemAdmin(UnfoldModelAdmin):
#     list_display = ("id", "stock", "product_item", "opening", "purchase", "sales", "returns", "damage", "stock_qty", "available", "value")
#     search_fields = ("product_item__product__product", "product_item__product__sku", "product_item__sku")
#     list_filter = ("stock", "product_item", "opening", "purchase", "sales", "returns", "damage")
#     readonly_fields = ("stock_qty", "available", "value")