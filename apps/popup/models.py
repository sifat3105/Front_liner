from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import date
from decimal import Decimal
from django.contrib.auth import get_user_model
User=get_user_model()


# Create your models here.

class Wallet(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE,related_name="wallet")
    message=models.CharField(max_length=255,blank=True,null=True,default="Please recharge.")
    balance = models.DecimalField(max_digits=12,decimal_places=2,default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.balance}"

# class Recharge(models.Model):
#     user = models.ForeignKey(User,on_delete=models.CASCADE,related_name="recharges")
#     amount = models.DecimalField(max_digits=10, decimal_places=2)
#     is_success = models.BooleanField(default=True)
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.user} - {self.amount}"
    



# wallet services
# def is_recharge_popup_required(wallet):
#     today = date.today()
#     day = today.day

#     if wallet.balance <= Decimal("0.00"):
#         return True, "INSUFFICIENT_BALANCE"

#     if 5 <= day <= 10:
#         return True, "MONTHLY_REMINDER"

#     return False, None

