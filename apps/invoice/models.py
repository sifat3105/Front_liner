from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Invoice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    STATUS_CHOICES = [
        ("paid", "Paid"),
        ("over_due", "Over Due"),
        ("pending", "Pending"),
        ("cancelled", "Cancelled"),
    ]

    customer = models.CharField(max_length=255)
    agent = models.CharField(max_length=255, blank=True, null=True)
    
    due_date = models.DateField()

    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    notes = models.TextField(blank=True, null=True)

    image = models.ImageField(upload_to="invoice_images/", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Invoice #{self.id} - {self.customer}"


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(
        Invoice,
        related_name="items",
        on_delete=models.CASCADE
    )

    description = models.CharField(max_length=255)
    qty = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    @property
    def total(self):
        return self.qty * self.unit_price

    def __str__(self):
        return f"{self.description} ({self.qty} × {self.unit_price})"
    
    
    



class AdminInvoice(models.Model):
    STATUS_CHOICES = [
        ("paid", "Paid"),
        ("unpaid", "Unpaid"),
        ("over_due", "Over Due"),
        ("pending", "Pending"),
    ]

    # The admin (superuser) who created the invoice
    created_by = models.ForeignKey(
        User,
        related_name="admin_invoices_created",
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={"is_staff": True}  # Only staff / superusers
    )

    # The normal user who receives the invoice
    assigned_to = models.ForeignKey(
        User,
        related_name="invoices",
        on_delete=models.CASCADE,
        limit_choices_to={"is_staff": False}  # Only regular users
    )

    invoice_number = models.CharField(max_length=50, unique=True)
    invoice_date = models.DateField()
    due_date = models.DateField()

    description = models.TextField(blank=True, null=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invoice {self.invoice_number} → {self.assigned_to.username}"
    
class AdminInvoiceItem(models.Model):
    invoice = models.ForeignKey(AdminInvoice, related_name="items", on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    qty = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    @property
    def total(self):
        return self.qty * self.unit_price

    def __str__(self):
        return self.description

