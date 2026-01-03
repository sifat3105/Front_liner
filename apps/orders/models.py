from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import Max
User = get_user_model()

BRAND_PREFIX = "FL"

STATUS_CHOICES = [
    ('WRONG_NUMBER', 'Wrong Number'),
    ('PENDING', 'Pending'),
    ('UNREACHABLE', 'Unreachable'),
]
ORDER_STATUS_CHOICES = [
    ('PENDING', 'Pending'),
    ('CONFIRM', 'Confirm'),
    ('CANCEL', 'Cancel'),
]

PLATFORM_CHOICES = [
    ('FACEBOOK', 'Facebook'),
    ('INSTAGRAM', 'Instagram'),
    ('TIKTOK', 'TikTok'),
    ('WEBSITE', 'Website'),
]

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_id = models.CharField(max_length=20, unique=True)
    customer = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    contact = models.CharField(max_length=20)
    order_amount = models.DecimalField(max_digits=10, decimal_places=2)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='PENDING')

    def __str__(self):
        return self.order_id

    def get_view_action(self):
        return f"/orders/{self.id}/view/"
    
    

    def save(self, *args, **kwargs):
        if not self.order_id:
            last_order = Order.objects.filter(
                order_id__startswith=f"{BRAND_PREFIX}-"
            ).aggregate(
                max_id=Max('order_id')
            )['max_id']

            if last_order:
                last_number = int(last_order.split('-')[1])
                self.order_id = f"{BRAND_PREFIX}-{last_number + 1}"
            else:
                self.order_id = f"{BRAND_PREFIX}-1001"

        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product_name = models.CharField(max_length=255)
    product_image = models.FileField(upload_to='product_images/', blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)
    color = models.CharField(max_length=50, blank=True, null=True)
    size = models.CharField(max_length=50, blank=True, null=True)
    weight = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)  # any extra info

    def __str__(self):
        return f"{self.product_name} ({self.quantity})"
