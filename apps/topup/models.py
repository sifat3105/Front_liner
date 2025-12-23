from django.db import models
from apps.transaction.models import Transaction

class Topup(models.Model):
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=100, unique=True)
    client_secret = models.CharField(max_length=200, blank=True, null=True)
    status = models.CharField(max_length=100, choices=[
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Topup {self.id}"