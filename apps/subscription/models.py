from django.conf import settings
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

class SubscriptionPlan(models.Model):
    INTERVAL_CHOICES = (
        ("day", "Day"),
        ("month", "Month"),
        ("year", "Year"),
    )

    name = models.CharField(max_length=80)  
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    interval = models.CharField(max_length=10, choices=INTERVAL_CHOICES, default="month")
    interval_count = models.PositiveIntegerField(default=1)  # e.g. 1 month, 3 months
    is_active = models.BooleanField(default=True)

    # feature flags (optional)
    features = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.interval_count} {self.interval})"


class UserSubscription(models.Model):
    STATUS_CHOICES = (
        ("active", "Active"),
        ("expired", "Expired"),
        ("canceled", "Canceled"),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="subscription",
    )
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="expired")

    started_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    last_renewed_at = models.DateTimeField(null=True, blank=True)

    def is_active(self) -> bool:
        if self.status != "active":
            return False
        if not self.expires_at:
            return False
        return timezone.now() < self.expires_at

    def mark_expired_if_needed(self):
        if self.status == "active" and self.expires_at and timezone.now() >= self.expires_at:
            self.status = "expired"
            self.save(update_fields=["status"])

    def __str__(self):
        return f"{self.user.email} -> {self.status}"
