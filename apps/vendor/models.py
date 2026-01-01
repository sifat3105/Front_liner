from django.db import models
from django.contrib.auth import get_user_model
User=get_user_model()
# Create your models here.


class Vendor(models.Model):

    owner = models.ForeignKey(User,on_delete=models.CASCADE,related_name='vendors')


    # -------- Shop Information --------
    shop_name = models.CharField(max_length=200)
    shop_description = models.TextField()
    business_email = models.EmailField()
    business_phone = models.CharField(max_length=20)
    business_address = models.TextField()

    # -------- Legal Information --------
    business_registration_number = models.CharField(max_length=100)
    tax_id = models.CharField(max_length=100)
    business_type = models.CharField(max_length=100)
    years_in_business = models.PositiveIntegerField()
    website_url = models.URLField(blank=True, null=True)

    # -------- Bank Information --------
    bank_name = models.CharField(max_length=150)
    account_holder_name = models.CharField(max_length=150)
    account_number = models.CharField(max_length=50)
    routing_number = models.CharField(max_length=50)
    swift_bic_code = models.CharField(max_length=50, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Vendor"
        verbose_name_plural = "Vendors"

    def __str__(self):
        return self.shop_name
