from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class PhoneNumber(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, unique=True)
    friendly_name = models.CharField(max_length=100, blank=True, default="")
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    number_sid = models.CharField(max_length=50, unique=True, null=True)
    
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    def __str__(self):
        return f"Phone Number: {self.phone_number} for User: {self.user.email}"
    
    
