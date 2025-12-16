from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()
# Create your models here.

class CustomerInfo(models.Model):
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sells',
        null=True,blank=True
    )

    # Status choices
    CUSTOMER_STATUS = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending'),
    ]

    # Platform choices (social media)
    PLATFORM_CHOICES = [
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('twitter', 'Twitter'),
        ('linkedin', 'LinkedIn'),
        ('tiktok', 'TikTok'),
        ('youtube', 'YouTube'),
    ]

    location = models.CharField(max_length=255)
    contact = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES)
    status = models.CharField(max_length=20, choices=CUSTOMER_STATUS, default='active')

    def __str__(self):
        return f"{self.location} ({self.id})"
