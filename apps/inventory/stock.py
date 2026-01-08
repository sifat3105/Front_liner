from django.db import models
from django.db.models import Sum
from inventory.models import Order,ProductPurchaseItem
from django.utils.crypto import get_random_string




class Stock(models.Model):

    product = models.OneToOneField(Order,on_delete=models.CASCADE,related_name="stock")
    purchease=models.OneToOneField(ProductPurchaseItem,on_delete=models.CASCADE,related_name="stock")


    sku = models.CharField(max_length=50,unique=True,editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = f"SKU-{get_random_string(8).upper()}"
        super().save(*args, **kwargs)

    @property
    def product_name(self):
        return self.product.product

    @property
    def product_image(self):
        return self.product.image.url if self.product.image else None

    @property
    def opening(self):
        return self.product.quantity or 0

    @property
    def purchase(self):
        return self.purchease.quantity.aggregate(
            total=Sum("quantity")
        )["total"] or 0

    @property
    def sales(self):
        return self.product.sales_items.aggregate(
            total=Sum("quantity")
        )["total"] or 0

    @property
    def c_return(self):
        return self.product.customer_returns.aggregate(
            total=Sum("quantity")
        )["total"] or 0

    @property
    def s_return(self):
        return self.product.supplier_returns.aggregate(
            total=Sum("quantity")
        )["total"] or 0

    @property
    def damage(self):
        return self.product.damages.aggregate(
            total=Sum("quantity")
        )["total"] or 0

    @property
    def balance(self):
        return (
            self.opening +
            self.purchase +
            self.c_return
            -
            (self.sales + self.s_return + self.damage)
        )

    @property
    def amount(self):
        return self.balance * self.product.price
