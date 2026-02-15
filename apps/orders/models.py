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

CALL_CONFIRMATION_STATUS_CHOICES = [
    ("PENDING", "Pending"),
    ("CALL_STARTED", "Call Started"),
    ("CONFIRMED", "Confirmed"),
    ("REJECTED", "Rejected"),
    ("FAILED", "Failed"),
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
    
    created_by = models.CharField(choices=(('seller', 'Seller'), ('bot', 'Bot')), max_length=10, default='bot')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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


class OrderCallConfirmation(models.Model):
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="call_confirmation",
    )
    call_sid = models.CharField(max_length=255, blank=True, null=True)
    from_number = models.CharField(max_length=50, blank=True, null=True)
    to_number = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=CALL_CONFIRMATION_STATUS_CHOICES,
        default="PENDING",
    )
    notes = models.TextField(blank=True, null=True)
    confirmed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="confirmed_order_calls",
        null=True,
        blank=True,
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)
    courier_booking_ref = models.CharField(max_length=100, blank=True, null=True)
    courier_booking_error = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.order.order_id} - {self.status}"
