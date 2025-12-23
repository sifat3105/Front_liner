from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
User = get_user_model()  

# Create your models here.

class Payment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('canceled', 'Canceled'),
    )

    # Linked with registered user
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE ,null=True, blank=True)
    invoice_number = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Customer info (auto filled from user profile)
    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=20)
    customer_email = models.EmailField()

    trx_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.invoice_number} - {self.user.username if self.user else 'Anonymous'}"

