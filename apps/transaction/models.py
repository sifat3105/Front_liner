from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transactions")
    status = models.CharField(max_length=100, choices=[
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ])
    category = models.CharField(max_length=100, choices=[
        ("topup", "Topup"),
        ("call", "Call"),
        ("agent", "Agent"),
        ("number", "Number"),
        ("support", "Support"),
        ("other", "Other"),
    ])
    transaction_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    description = models.CharField(max_length=100, blank=True, null=True)
    purpose = models.CharField(max_length=100, blank=True, null=True)
    payment_method = models.CharField(max_length=100, choices=[
        ("credit_card", "Credit Card"),
        ("bank_transfer", "Bank Transfer"),
        ("cash", "Cash"),
        ("balance", "Balance"),
        ("other", "Other"),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.transaction_id} - {self.status} - {self.amount}"
    