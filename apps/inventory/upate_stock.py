from django.db.models import Sum
from .models import Product, ProductItem, Stock, StockItem, PurchaseReturnItem
from django.db import transaction


def update_stock_opening(instance):
    product = instance
    opening_qty = sum(
        item.quantity for item in product.items.all() if (item.quantity or 0) > 0
    )

    # Either create or update stock
    Stock.objects.update_or_create(
        product=product,
        defaults={
            "opening": opening_qty,
            "purchase": 0,
            "customer_return": 0,
            "sales": 0,
            "supplier_return": 0,
            "damage": 0,
            "balance": 0,
            "amount": 0,
        }
    )


def update_stock_on_purchase(product, ):
    
    stock = Stock.objects.select_for_update().get(
        product=product
    )
