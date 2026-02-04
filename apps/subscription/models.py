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

    def has_permission(self, code: str) -> bool:
        return self.permissions.filter(code=code, is_active=True).exists()

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

    def has_permission(self, code: str) -> bool:
        if not self.is_active() or not self.plan_id:
            return False
        return self.plan.has_permission(code)

    def __str__(self):
        return f"{self.user.email} -> {self.status}"
    
    
class SubscriptionPermission(models.Model):
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.CASCADE,
        related_name="permissions",
    )
    code = models.SlugField(max_length=80)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("plan", "code")
        ordering = ("name", "id")

    def __str__(self):
        return f"{self.plan.name}: {self.name} ({self.code})"
