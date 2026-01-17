from django.db import models
from django.utils import timezone
from apps.vendor.models import Vendor
from django.contrib.auth import get_user_model
from django.db.models import Sum, F
import re


User=get_user_model()


def clean_text(text, length):
    text = re.sub(r"[^A-Za-z0-9]", "", text)
    return text.upper()[:length]


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
    
    sku = models.CharField(max_length=100,blank=True,null=True, unique=True, db_index=True)
    barcode = models.ImageField(upload_to="barcodes/", blank=True, null=True)
    qr_code = models.ImageField(upload_to="qrcodes/", blank=True, null=True)
    
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default='draft')

    created = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.product
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None

        super().save(*args, **kwargs)

        if is_new and not self.sku:
            vendor_code = clean_text(self.vendor.shop_name, 2)
            product_code = clean_text(self.product, 3)

            self.sku = f"FL-{vendor_code}-{product_code}-{self.id:06d}"

            super().save(update_fields=["sku"])
            
            
            
class ProductItem(models.Model):
    product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name="items")
    size = models.CharField(max_length=20, blank=True, null=True)
    color = models.CharField(max_length=20, blank=True, null=True)
    quantity = models.IntegerField(default=0,blank=True,null=True)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2,blank=True,null=True)
    sell_price = models.DecimalField(max_digits=10, decimal_places=2,blank=True,null=True)
    
    sku = models.CharField(max_length=100,blank=True,null=True, unique=True, db_index=True)
    barcode = models.ImageField(upload_to="barcodes/", blank=True, null=True)
    qr_code = models.ImageField(upload_to="qrcodes/", blank=True, null=True)
    
    def __str__(self):
        return f"{self.product.sku} - {self.size} - {self.color}"
    


class ProductPurchase(models.Model):
    vendor = models.ForeignKey(Vendor,on_delete=models.CASCADE,related_name="purchases")
    purchase_id = models.CharField(max_length=100, blank=True, null=True)
    order_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    items = models.JSONField(default=dict, blank=True)
    total_acount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"PO-{self.id} | {self.vendor}"
    


class ProductPurchaseItem(models.Model):
    purchase = models.ForeignKey(ProductPurchase,on_delete=models.CASCADE,related_name="purchase_items")
    product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name="purchase_items")
    quantity = models.PositiveIntegerField(default=0)

    

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
    
    
class StockItem(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name="items")
    product_item = models.ForeignKey(ProductItem, on_delete=models.CASCADE, related_name="stock_item")
    
    opening = models.PositiveIntegerField(default=0)
    purchase = models.PositiveIntegerField(default=0)
    sales = models.PositiveIntegerField(default=0)
    returns = models.PositiveIntegerField(default=0)
    damage = models.PositiveIntegerField(default=0)
    

    @property
    def stock_qty(self):
        """Current stock for this item"""
        return self.opening + self.purchase - self.returns - self.sales - self.damage

    @property
    def available(self):
        """Available stock"""
        return self.stock_qty

    @property
    def value(self):
        """Total value for this stock item"""
        return self.available * self.product_item.price

    def __str__(self):
        return f"{self.product_item.sku} in {self.stock.product.product}"
    
    
class StockMovement(models.Model):
    MOVEMENT_TYPE = (
        ("OPENING", "Opening"),
        ("PURCHASE", "Purchase"),
        ("SALE", "Sale"),
        ("CUSTOMER_RETURN", "Customer Return"),
        ("SUPPLIER_RETURN", "Supplier Return"),
        ("DAMAGE", "Damage"),
    )

#     product = models.ForeignKey(Product, on_delete=models.CASCADE)
#     movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE)
#     quantity = models.IntegerField()
#     unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

#     created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.sku} - {self.movement_type}"
    
    

class PurchaseReturn(models.Model):
    purchase_order = models.ForeignKey( ProductPurchase, on_delete=models.CASCADE, related_name="returns")
    
    return_number = models.CharField( max_length=50, unique=True, blank=True)
    return_date = models.DateField(auto_now_add=True)
    reason = models.TextField(blank=True, null=True)


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"PR-{self.id} "
    

    @property
    def total_amount(self):
        return self.items.aggregate(total=Sum(F("product_item__unit_cost") * F("quantity")))["total"]

    
    @property
    def total_items(self):
        return self.items.count()
    
    @property
    def total_qty(self):
        return self.items.aggregate(total=Sum("quantity"))["total"]
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new and not self.return_number:
            self.return_number = f"PR-{self.id:06d}"
            super().save(update_fields=["return_number"])

        





class PurchaseReturnItem(models.Model):
    purchase_return = models.ForeignKey( PurchaseReturn, on_delete=models.CASCADE, related_name="items")

    product_item = models.ForeignKey(ProductItem, on_delete=models.CASCADE)

    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product_item.sku} - {self.quantity}"
    
    @property
    def total_price(self):
        return self.quantity * self.product_item.unit_cost
    
class LossAndDamage(models.Model):
    purchase_order = models.ForeignKey( ProductPurchase, on_delete=models.CASCADE, related_name='loss_and_damage')
    
    damage_number = models.CharField( max_length=50, unique=True, blank=True)
    damage_date = models.DateField(auto_now_add=True)
    damage_type = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"LD-{self.id} "
    
    @property
    def total_items(self):
        return self.items.count()
    
    @property
    def total_qty(self):
        return self.items.aggregate(total=Sum("quantity"))["total"]
    
    @property
    def total_amount(self):
        return self.items.aggregate(total=Sum(F("product_item__unit_cost") * F("quantity")))["total"]
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new and not self.damage_number:
            self.damage_number = f"DMG-{self.id:06d}"
            super().save(update_fields=["damage_number"])
    
    
    
class LossAndDamageItem(models.Model):
    loss_and_damage = models.ForeignKey( LossAndDamage, on_delete=models.CASCADE, related_name="items")
    
    product_item = models.ForeignKey(ProductItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    condition_notes = models.TextField(blank=True, null=True)
    
    @property
    def total_price(self):
        return self.quantity * self.product_item.unit_cost