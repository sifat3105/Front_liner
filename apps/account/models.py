from django.db import models, transaction
from django.contrib.auth.models import User
from django.db.models import Sum
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()

# Incom section

class Income(models.Model):
    owner = models.ForeignKey(User,on_delete=models.CASCADE,related_name="incomes")
    date = models.DateField()
    customer = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12,decimal_places=2,default=0)
    payment_method = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        verbose_name = "Income"
        verbose_name_plural = "Incomes"

    def __str__(self):
        return f"{self.customer} - {self.amount}"


class Payments(models.Model):

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payments',
        null=True,blank=True
    )
    
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('bank', 'Bank Transfer'),
        ('paypal', 'Paypal'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]

    date = models.DateField()
    customer = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.customer} - {self.amount}"

# SELL Model
class Sells(models.Model):
    owner = models.ForeignKey(User,on_delete=models.CASCADE,related_name='Sells',null=True, blank=True)

    # Status choices
    CUSTOMER_STATUS = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending'),
    ]

    # Platform choices
    PLATFORM_CHOICES = [
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('twitter', 'Twitter'),
        ('linkedin', 'LinkedIn'),
        ('tiktok', 'TikTok'),
        ('youtube', 'YouTube'),
    ]

      # Sells status
    SELLS_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]
    
    order_id=models.CharField(max_length=10,blank=True,null=True)
    customer= models.CharField(max_length=255,blank=True,null=True)
    location = models.CharField(max_length=255)
    contact = models.CharField(max_length=50)
    order_amount = models.DecimalField(max_digits=10, decimal_places=2)
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES)
    sells_status = models.CharField(max_length=20, choices=SELLS_STATUS, default='pending')

    def __str__(self):
        return f"{self.owner} - {self.location} ({self.id})"
    
# Refund Orders
class Refund(models.Model):
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='Refund',
        null=True, blank=True
    )

    # Status choices
    CUSTOMER_STATUS = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending'),
    ]

    # Platform choices
    PLATFORM_CHOICES = [
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('twitter', 'Twitter'),
        ('linkedin', 'LinkedIn'),
        ('tiktok', 'TikTok'),
        ('youtube', 'YouTube'),
    ]
        # Refund status
    REFUND_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('Eligible', 'Eligible'),
        ('rejected', 'Rejected'),
    ]

    order_id=models.CharField(max_length=10,blank=True,null=True)
    customer= models.CharField(max_length=255,blank=True,null=True)
    location = models.CharField(max_length=255)
    contact = models.CharField(max_length=50)
    order_amount = models.DecimalField(max_digits=10, decimal_places=2)
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES)

    refund_status = models.CharField(max_length=20, choices=REFUND_STATUS, default='pending')

    def __str__(self):
        return f"{self.owner} - {self.location} ({self.id})"
    
# Debit Credit section

class DebitCredit(models.Model):

    PAYMENT_TYPE = (
        ('cash', 'Cash'),
        ('bank', 'Bank'),
    )

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ledger_entries'
    )

    voucher_no = models.CharField(max_length=20)
    customer_name = models.CharField(max_length=255)

    payment_description = models.TextField(blank=True, null=True)

    payment_type = models.CharField(
        max_length=10,
        choices=PAYMENT_TYPE
    )

    invoice_no = models.CharField(max_length=100, blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)


    debit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        editable=False
    )

    credit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        editable=False
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        editable=False
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def clean(self):
        if not self.payment_type:
            raise ValidationError({"payment_type": "Payment type is required."})
        if self.amount <= 0:
            raise ValidationError({"amount": "Amount must be greater than zero."})

    def save(self, *args, **kwargs):
        with transaction.atomic():

            # Auto debit / credit
            if self.payment_type == 'debit':
                self.debit = self.amount
                self.credit = Decimal('0.00')

            elif self.payment_type == 'credit':
                self.credit = self.amount
                self.debit = Decimal('0.00')

            super().save(*args, **kwargs)

            # Auto balance (customer wise)
            totals = DebitCredit.objects.filter(
                owner=self.owner,
                customer_name=self.customer_name
            ).aggregate(
                total_debit=Sum('debit'),
                total_credit=Sum('credit')
            )

            balance = (
                (totals['total_debit'] or Decimal('0.00')) -
                (totals['total_credit'] or Decimal('0.00'))
            )

            DebitCredit.objects.filter(pk=self.pk).update(balance=balance)


# Profit & Loss (P&L) sectiont
class ProfitLossReport(models.Model):

    STATUS_CHOICES = (
        ('Profit', 'Profit'),
        ('Loss', 'Loss'),
        ('approved', 'Approved'),
    )

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='profit_loss_reports'
    )

    # Report Date
    date = models.DateField()

    # Financial Fields
    revenue = models.DecimalField(max_digits=15,decimal_places=2,default=0)
    expenses = models.DecimalField(max_digits=15,decimal_places=2,default=0)


    # Calculated Fields
    gross_profit = models.DecimalField(max_digits=15,decimal_places=2,default=0)
    net_profit = models.DecimalField(max_digits=15,decimal_places=2,default=0)


    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        verbose_name = "Profit & Loss Report"
        verbose_name_plural = "Profit & Loss Reports"

        
    @property
    def gross_profit(self):
        return self.revenue - self.expenses

    @property
    def net_profit(self):
        return self.revenue - self.expenses

    def __str__(self):
        return f"P&L Report - {self.date}"


# Payment section
class Receiver(models.Model):
    """
    Receiver can be a User or Supplier
    """

    RECEIVER_TYPE_CHOICES = (
        ('user', 'User'),
        ('supplier', 'Supplier'),
    )

    name = models.CharField(max_length=100)
    receiver_type = models.CharField(
        max_length=10,
        choices=RECEIVER_TYPE_CHOICES
    )

    def __str__(self):
        return f"{self.name} ({self.receiver_type})"


class Product(models.Model):

    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Invoice(models.Model):


    invoice_number = models.CharField(max_length=50, unique=True)
    receiver = models.ForeignKey(
        Receiver,
        on_delete=models.CASCADE,
        related_name='invoices'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.invoice_number


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = (
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
        ('gateway', 'Gateway'),
    )

    receiver = models.ForeignKey(
        Receiver,
        on_delete=models.CASCADE,
        related_name='payments',
        null=True,       # old rows-এর জন্য null allow
        blank=True
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True
    )

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    description = models.TextField(blank=True,null=True)

    quantity = models.PositiveIntegerField(default=1)

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0   # old rows-এর জন্য default
    )

    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_METHOD_CHOICES,
        default='cash'   # old rows-এর জন্য default
    )

    cheque_number = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment #{self.id}"
