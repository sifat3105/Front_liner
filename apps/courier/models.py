from django.db import models
from django.contrib.auth import get_user_model
User=get_user_model()
# Create your models here.


# courier list model
class Courierlist(models.Model):
    name = models.CharField(max_length=255, unique=True)
    logo = models.ImageField(upload_to='courier_logos/', blank=True, null=True)
    is_active = models.BooleanField(default=True)  # active/inactive status
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def toggle_status(self):
        self.is_active = not self.is_active
        self.save()

    def __str__(self):
        return self.name

class UserCourier(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    courier_list = models.ManyToManyField(Courierlist, blank=True)

    def __str__(self):
        return f"{getattr(self.user, 'username', str(self.user))}'s Courier Companies"




# Merchant Registration Model PAPERFLY
class PaperflyMerchant(models.Model):
    merchant_name = models.CharField(max_length=255)
    product_nature = models.CharField(max_length=255)
    address = models.TextField()
    thana = models.CharField(max_length=255)
    district = models.CharField(max_length=255)
    website = models.URLField(blank=True, null=True)
    facebook = models.URLField(blank=True, null=True)
    company_phone = models.CharField(max_length=50, blank=True, null=True)
    contact_name = models.CharField(max_length=255, blank=True, null=True)
    designation = models.CharField(max_length=255, blank=True, null=True)
    contact_number = models.CharField(max_length=50)
    email = models.EmailField(blank=True, null=True)
    account_name = models.CharField(max_length=255, blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    bank_name = models.CharField(max_length=255)
    bank_branch = models.CharField(max_length=255)
    routing_number = models.CharField(max_length=50, blank=True, null=True)
    payment_mode = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.merchant_name

# order submission integration Model PAPERFLY
class PaperflyOrder(models.Model):
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    merchantCode = models.CharField(max_length=50)
    merOrderRef = models.CharField(max_length=50)
    pickMerchantName = models.CharField(max_length=255, blank=True, null=True)
    pickMerchantAddress = models.TextField(blank=True, null=True)
    pickMerchantThana = models.CharField(max_length=255, blank=True, null=True)
    pickMerchantDistrict = models.CharField(max_length=255, blank=True, null=True)
    pickupMerchantPhone = models.CharField(max_length=50, blank=True, null=True)
    productSizeWeight = models.CharField(max_length=50)
    productBrief = models.CharField(max_length=255, blank=True, null=True)
    packagePrice = models.CharField(max_length=50)
    deliveryOption = models.CharField(max_length=50)
    custname = models.CharField(max_length=255)
    custaddress = models.TextField()
    customerThana = models.CharField(max_length=255, blank=True, null=True)
    customerDistrict = models.CharField(max_length=255)
    custPhone = models.CharField(max_length=50)
    max_weight = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.merOrderRef

#  Order Tracking Model PAPERFLY
class PaperflyOrderTracking(models.Model):
    ReferenceNumber = models.CharField(max_length=50)
    merchantCode = models.CharField(max_length=50)

    # Status fields from API response
    Pick = models.CharField(max_length=255, blank=True, null=True)
    PickTime = models.CharField(max_length=50, blank=True, null=True)
    inTransit = models.CharField(max_length=255, blank=True, null=True)
    inTransitTime = models.CharField(max_length=50, blank=True, null=True)
    ReceivedAtPoint = models.CharField(max_length=255, blank=True, null=True)
    ReceivedAtPointTime = models.CharField(max_length=50, blank=True, null=True)
    PickedForDelivery = models.CharField(max_length=255, blank=True, null=True)
    PickedForDeliveryTime = models.CharField(max_length=50, blank=True, null=True)
    Delivered = models.CharField(max_length=255, blank=True, null=True)
    DeliveredTime = models.CharField(max_length=50, blank=True, null=True)
    Returned = models.CharField(max_length=255, blank=True, null=True)
    ReturnedTime = models.CharField(max_length=50, blank=True, null=True)
    Partial = models.CharField(max_length=255, blank=True, null=True)
    PartialTime = models.CharField(max_length=50, blank=True, null=True)
    onHoldSchedule = models.CharField(max_length=255, blank=True, null=True)
    close = models.CharField(max_length=255, blank=True, null=True)
    closeTime = models.CharField(max_length=50, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ReferenceNumber} - {self.merchantCode}"

# order cancellation integration PAPERFLY
class PaperflyOrderCancel(models.Model):
    order_id = models.CharField(max_length=50)
    merchantCode = models.CharField(max_length=50)
    cancel_message = models.CharField(max_length=255, blank=True, null=True)
    response_code = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.order_id



# ORDER MODEL STEDFAST
class SteadfastOrder(models.Model):
    consignment_id = models.BigIntegerField(null=True, blank=True)
    invoice = models.CharField(max_length=100, null=True, blank=True)
    tracking_code = models.CharField(max_length=100, null=True, blank=True)
    recipient_name = models.CharField(max_length=100)
    recipient_phone = models.CharField(max_length=20)
    recipient_address = models.TextField()
    cod_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=50, default="in_review")
    note = models.TextField(null=True, blank=True)
    api_response = models.TextField(null=True, blank=True)  # Save JSON as text
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.invoice or str(self.consignment_id)

# TRACKING MODEL STEDFAST
class SteadfastTracking(models.Model):
    consignment_id = models.BigIntegerField(null=True, blank=True)
    invoice = models.CharField(max_length=100, null=True, blank=True)
    tracking_code = models.CharField(max_length=100, null=True, blank=True)
    delivery_status = models.CharField(max_length=50)
    api_response = models.TextField(null=True, blank=True)  # Save JSON as text
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.consignment_id

# RETURN REQUEST MODEL STEDFAST
class SteadfastReturnRequest(models.Model):
    return_id = models.BigIntegerField(null=True, blank=True)
    consignment_id = models.BigIntegerField(null=True, blank=True)
    invoice = models.CharField(max_length=100, null=True, blank=True)
    tracking_code = models.CharField(max_length=100, null=True, blank=True)
    reason = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=50, default="pending")
    api_response = models.TextField(null=True, blank=True)  # Save JSON as text
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.return_id


# ===============================
# PATHAO TOKEN
# ===============================
class PathaoToken(models.Model):
    access_token = models.TextField()
    refresh_token = models.TextField()
    expires_in = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Token {self.id}"

# PATHAO STORE
class PathaoStore(models.Model):
    store_id = models.CharField(max_length=100, unique=True)
    store_name = models.CharField(max_length=255)
    store_address = models.TextField()
    city_id = models.IntegerField()
    zone_id = models.IntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.store_name

# PATHAO ORDER
class PathaoOrder(models.Model):
    consignment_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    merchant_order_id = models.CharField(max_length=100)
    store = models.ForeignKey(PathaoStore, on_delete=models.CASCADE, related_name='orders')
    order_status = models.CharField(max_length=50, default="Pending")
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.merchant_order_id} ({self.order_status})"


