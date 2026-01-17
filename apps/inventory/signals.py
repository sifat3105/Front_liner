from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Product, ProductItem, Stock
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
        
        
# @receiver(post_save, sender=ProductItem)
# def update_stock_on_item_save(sender, instance, created, **kwargs):
#     product = instance.product
#     opening_qty = sum(
#         item.quantity for item in product.items.all() if (item.quantity or 0) > 0
#     )
    
#     # Either create or update stock
#     Stock.objects.update_or_create(
#         product=product,
#         defaults={
#             "opening": opening_qty,
#             "purchase": 0,
#             "customer_return": 0,
#             "sales": 0,
#             "supplier_return": 0,
#             "damage": 0,
#             "balance": 0,
#             "amount": 0,
#         }
#     )