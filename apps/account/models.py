from django.db import models
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

    location = models.CharField(max_length=255)
    contact = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES)
    # Refund status
    REFUND_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]
    sells_status = models.CharField(max_length=20, choices=REFUND_STATUS, default='pending')

    def __str__(self):
        return f"{self.owner} - {self.location} ({self.id})"
    


# Refund Orders
class CustomerRefund(models.Model):
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

    location = models.CharField(max_length=255)
    contact = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES)
    # Refund status
    REFUND_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('Eligible', 'Eligible'),
        ('rejected', 'Rejected'),
    ]
    refund_status = models.CharField(max_length=20, choices=REFUND_STATUS, default='pending')

    def __str__(self):
        return f"{self.owner} - {self.location} ({self.id})"
    


# Debit Credit section
class VoucherType(models.Model):

    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class VoucherEntry(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    VOUCHER_NATURE = (
        ('debit', 'Debit'),
        ('credit', 'Credit'),
    )

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='vouchers'
    )

    voucher_no = models.CharField(max_length=100, unique=True)
    voucher_date = models.DateField()

    customer_name = models.CharField(max_length=255)

    voucher_type = models.ForeignKey(
        VoucherType,
        on_delete=models.PROTECT,
        related_name='vouchers'
    )

    nature = models.CharField(
        max_length=10,
        choices=VOUCHER_NATURE
    )

    debit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    credit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    total_debit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    total_credit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    posted = models.BooleanField(default=False)

    due_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.voucher_no} - {self.customer_name}"
    

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
    revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    expenses = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    operating_expenses = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    # Calculated Fields
    gross_profit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        verbose_name = "Profit & Loss Report"
        verbose_name_plural = "Profit & Loss Reports"

    def save(self, *args, **kwargs):

        # Gross Profit = Revenue - Expenses
        self.gross_profit = self.revenue - self.expenses

        # Net Profit = Gross Profit - Operating Expenses
        self.net_profit = self.gross_profit - self.operating_expenses

        super().save(*args, **kwargs)

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
