from django.core.management.base import BaseCommand
from apps.inventory.models import ProductItem
from apps.inventory.signals import clean_text

class Command(BaseCommand):
    help = "Generate SKU for existing products"

    def handle(self, *args, **kwargs):
        products = ProductItem.objects.filter(sku__isnull=True)
        for product in products:
            vendor_code = clean_text(product.product.vendor.shop_name, 2)
            product_code = clean_text(product.product.product, 3)
            size_code = clean_text(product.size[0] if product.size else "NA", 3)
            color_code = clean_text(product.color[0] if product.color else "NA", 3)

            sku = f"FL-{vendor_code}-{product_code}-{color_code}-{size_code}-{product.id:04d}"

            product.save(update_fields=["sku"])
            self.stdout.write(self.style.SUCCESS(f"SKU generated for {product.id}"))
