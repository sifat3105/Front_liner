from rest_framework.exceptions import APIException

class PaymentRequired(APIException):
    status_code = 402
    default_detail = "Subscription expired. Please recharge to continue."
    default_code = "payment_required"
