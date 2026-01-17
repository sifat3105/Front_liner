from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Product, ProductItem, Stock, StockItem, PurchaseReturnItem
from django.db import transaction


from .utils import generate_barcode, generate_qr
import re
def clean_text(text, length):
    text = re.sub(r"[^A-Za-z0-9]", "", text)
    return text.upper()[:length]


@receiver(post_save, sender=Product)
def generate_sku_and_codes(sender, instance, created, **kwargs):
    if created and not instance.sku:
        vendor_code = clean_text(instance.vendor.shop_name, 2)
        product_code = clean_text(instance.product, 3)

        sku = f"FL-{vendor_code}-{product_code}-{instance.id:06d}"

        instance.sku = sku
        instance.barcode = generate_barcode(sku)
        instance.qr_code = generate_qr(sku)

        instance.save(update_fields=["sku", "barcode", "qr_code"])
        
        
        
@receiver(post_save, sender=ProductItem)
def generate_sku_and_codes_item(sender, instance, created, **kwargs):
    if created and not instance.sku:
        vendor_code = clean_text(instance.product.vendor.shop_name, 2)
        product_code = clean_text(instance.product.product, 3)
        size_code = clean_text(instance.size, 3)
        color_code = clean_text(instance.color, 3)

        sku = f"FL-{vendor_code}-{product_code}-{color_code}-{size_code}-{instance.id:04d}"

        instance.sku = sku
        instance.barcode = generate_barcode(sku)
        instance.qr_code = generate_qr(sku)

        instance.save(update_fields=["sku", "barcode", "qr_code"])
        



@receiver(post_save, sender=PurchaseReturnItem)
def update_stock_on_purchase_return(sender, instance, created, **kwargs):
    if not created:
        return
    print(instance.product_item)
    with transaction.atomic():
        product_item = instance.product_item
        qty = instance.quantity

        # --- PRODUCT LEVEL STOCK ---
        stock = Stock.objects.select_for_update().get(
            product=product_item.product
        )

        stock.supplier_return += qty
        stock.save()

        # --- ITEM LEVEL STOCK ---
        print(product_item.stock_item)
        stock_item = StockItem.objects.select_for_update().get(
            product_item=product_item
        )

        stock_item.returns += qty  
        stock_item.save()