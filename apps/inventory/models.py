from django.db import models
from django.utils import timezone
from apps.vendor.models import Vendor
from django.contrib.auth import get_user_model
User=get_user_model()

# Create your models here.

class Size(models.Model):
    size = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.size


class Color(models.Model):
    colors = models.CharField(max_length=30, unique=True)
    code = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="Hex code like #FF0000"
    )

    def __str__(self):
        return self.colors

class Product(models.Model):
    STATUS_CHOICES = (
        ('published', 'Published'),
        ('draft', 'Draft'),
    )

    vendor = models.ForeignKey(Vendor,on_delete=models.CASCADE,related_name='orders')
    image = models.ImageField(upload_to='orders/',blank=True,null=True)
    product = models.CharField(max_length=255)
    short_description = models.TextField(blank=True,null=True)
    brand = models.CharField(max_length=100,blank=True,null=True)
    quantity = models.IntegerField(default=0,blank=True,null=True)
    campaign = models.CharField(max_length=100,blank=True,null=True)

    price = models.DecimalField(max_digits=10, decimal_places=2,blank=True,null=True)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2,blank=True,null=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2,blank=True,null=True)

    sizes = models.JSONField(default=list, blank=True, null=True)

    colors = models.JSONField(default=list, blank=True, null=True)

    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default='draft')

    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.product


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


