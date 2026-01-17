from django.db import models
from django.utils import timezone
from apps.vendor.models import Vendor
from django.contrib.auth import get_user_model
User=get_user_model()


# Create your models here.


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

    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default='draft')

    created = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.product
    
class ProductItem(models.Model):
    product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name="items")
    size = models.JSONField(default=list, blank=True, null=True)
    color = models.JSONField(default=list, blank=True, null=True)
    quantity = models.IntegerField(default=0,blank=True,null=True)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2,blank=True,null=True)
    


# PRODUCT PURCHASE

class OrderItem(models.Model):
    order = models.ForeignKey(ProductItem, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_items')

    size = models.CharField(max_length=50)
    color = models.CharField(max_length=50)

    quantity = models.PositiveIntegerField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    sell_price = models.DecimalField(max_digits=10, decimal_places=2)

    total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"OrderItem #{self.id} (Order {self.order_id})"

    

# class Stock(models.Model):
#     product = models.OneToOneField(
#         Product,
#         on_delete=models.CASCADE,
#         related_name="stock"
#     )

#     opening = models.PositiveIntegerField(default=0)
#     purchase = models.PositiveIntegerField(default=0)
#     customer_return = models.PositiveIntegerField(default=0)

#     sales = models.PositiveIntegerField(default=0)
#     supplier_return = models.PositiveIntegerField(default=0)
#     damage = models.PositiveIntegerField(default=0)

#     balance = models.IntegerField(default=0)
#     amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

#     updated_at = models.DateTimeField(auto_now=True)

#     def calculate_balance(self):
#         return (
#             self.opening
#             + self.purchase
#             + self.customer_return
#             - self.sales
#             - self.supplier_return
#             - self.damage
#         )

#     def save(self, *args, **kwargs):
#         self.balance = self.calculate_balance()
#         super().save(*args, **kwargs)

#     def __str__(self):
#         return f"Stock - {self.product.sku}"
    
    
# class StockMovement(models.Model):
#     MOVEMENT_TYPE = (
#         ("OPENING", "Opening"),
#         ("PURCHASE", "Purchase"),
#         ("SALE", "Sale"),
#         ("CUSTOMER_RETURN", "Customer Return"),
#         ("SUPPLIER_RETURN", "Supplier Return"),
#         ("DAMAGE", "Damage"),
#     )

#     product = models.ForeignKey(Product, on_delete=models.CASCADE)
#     movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE)
#     quantity = models.IntegerField()
#     unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.product.sku} - {self.movement_type}"




