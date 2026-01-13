from django.db import models
from django.utils import timezone
from apps.vendor.models import Vendor
from django.contrib.auth import get_user_model
User=get_user_model()

# Create your models here.


class Product(models.Model):
    STATUS_CHOICES = (
        ("Draft", "Draft"),
        ("Published", "Published"),
    )

    vendor = models.ForeignKey(Vendor,on_delete=models.CASCADE,related_name="products",null=True,blank=True)
    product = models.CharField(max_length=255)
    short_description = models.TextField(blank=True)
    # brand = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10,decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Draft")

    image = models.ImageField(upload_to="products/",null=True,blank=True)

    created_at = models.DateTimeField(auto_now_add=True,null=True,blank=True)
    updated_at = models.DateTimeField(auto_now=True,null=True,blank=True)

    def __str__(self):
        return f"{self.product} ({self.brand})"



class ProductItem(models.Model):
    product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name="items")
    size = models.CharField(max_length=50)
    color = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField(default=0)
    unit_cost = models.DecimalField(max_digits=10,decimal_places=2)


    def __str__(self):
        return f"{self.product.product} | {self.size} | {self.color}"


# PRODUCT PURCHASE
class ProductPurchase(models.Model):
    vendor = models.ForeignKey(Vendor,on_delete=models.CASCADE,related_name="purchases")
    order_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PO-{self.id} | {self.vendor}"


# PURCHASE ITEMS
class ProductPurchaseItem(models.Model):
    purchase = models.ForeignKey(ProductPurchase,on_delete=models.CASCADE,related_name="items")
    product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name="purchase_items")
    variant = models.CharField(max_length=100, blank=True, null=True)

    quantity = models.PositiveIntegerField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)


    def save(self, *args, **kwargs):
        self.total = self.quantity * self.unit_cost
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product} ({self.quantity})"


