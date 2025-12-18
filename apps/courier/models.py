from django.db import models

# Create your models here.


# Merchant Registration Model
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


# order submission integration Model
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



#  Order Tracking Model
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


# order cancellation integration
class PaperflyOrderCancel(models.Model):
    order_id = models.CharField(max_length=50)
    merchantCode = models.CharField(max_length=50)
    cancel_message = models.CharField(max_length=255, blank=True, null=True)
    response_code = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.order_id
