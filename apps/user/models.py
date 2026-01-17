
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.db.models import JSONField
import uuid
from django.core.exceptions import ValidationError


ROLE_CHOICES = (
    ("user", "User"),
    ("admin", "Admin"),
    ("superuser", "Superuser"),
    ("staff", "Staff"),
    ("seller", "Seller"),
    ("sub_seller", "Sub Seller"),
    ("reseller", "Reseller"),
    ("sub_reseller", "Sub_Reseller"),
    ("merchant", "Merchant"),
    ("sub_merchant", "Sub Merchant"),
)

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_staffuser(self, email, password=None):
        return self.create_user(email, password, is_staff=True)

    def create_superuser(self, email, password=None):
        return self.create_user(email, password, is_staff=True, is_superuser=True)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    objects = UserManager()
    USERNAME_FIELD = 'email'

    refer_token = models.CharField(max_length=255, blank=True, null=True)
    refer_user = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='referred_users')
    role = models.CharField(max_length=255, choices=ROLE_CHOICES, default="user")
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children')

    def __str__(self):
        return self.email
    
    def clean(self):

        # reseller to only sub_reseller
        if self.parent and self.parent.role == "reseller":
            if self.role != "sub_reseller":
                raise ValidationError({
                    "role": "Reseller can create only sub reseller"
                })

        # sub_reseller to cannot create anyone
        if self.parent and self.parent.role == "sub_reseller":
            raise ValidationError({
                "parent": "Sub reseller cannot create any user"
            })
        

    # ENFORCE clean() EVERYWHERE (API / ADMIN / SHELL)
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


    def get_all_users(self):
        """Return all users under this seller/sub_seller recursively."""
        users = []
        for child in self.children.all():
            if child.role == 'user':
                users.append(child)
            else:
                users.extend(child.get_all_users())
        return users

    def has_perm(self, perm, obj=None):
        return self.is_superuser or self.is_staff

    def has_module_perms(self, app_label):
        return self.is_superuser or self.is_staff
    
    @property
    def username(self):
        return self.email

class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="account")
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, null=True, blank=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    organization = models.CharField(max_length=255, null=True, blank=True)
    user_str_id= models.CharField(max_length=255, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    preferences = JSONField(default=dict, blank=True)
    last_login = models.DateTimeField(blank=True, null=True)
    date_joined = models.DateTimeField(default=timezone.now)
    image = models.ImageField(upload_to="user/profile/", blank=True, null=True)

    def __str__(self):
        return f"{self.user.email} Account"
    
    # def save(self, *args, **kwargs):
    #     self.user_id = uuid


class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.CharField(max_length=50)
    start_date = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    auto_renew = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.email} - {self.plan}"


# Setting > Profile > Shop Info Model
class Shop(models.Model):

    owner = models.ForeignKey(User,on_delete=models.CASCADE,related_name="shop")

    shop_name = models.CharField(max_length=255)
    shop_description = models.TextField(blank=True, null=True)
    business_email = models.EmailField()
    business_phone = models.CharField(max_length=20)
    business_address = models.TextField()
    website_url = models.URLField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.shop_name

# Setting > Profile > business Info Model
class Business(models.Model):

    owner = models.ForeignKey(User,on_delete=models.CASCADE,related_name="business")

    business_type = models.CharField(max_length=255)
    years_in_business = models.CharField(max_length=255)
    business_registration_number = models.CharField(max_length=100)
    tax_id_ein =  models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.business_type

# Setting > Profile > Banking Info Model
class Banking(models.Model):
    owner = models.ForeignKey(User,on_delete=models.CASCADE,related_name="Banking")

    bank_name = models.CharField(max_length=255)
    account_name =models.CharField(max_length=255)
    account_number = models.IntegerField()
    routing_number = models.IntegerField()
    swift_bic_code = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.bank_name