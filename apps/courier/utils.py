import requests
from django.conf import settings
from requests.auth import HTTPBasicAuth

from .models import PaperflyOrder ,SteadfastOrder,PathaoOrder 

def create_courier_order(
    merchantCode: str,
    merOrderRef: str,
    productSizeWeight: str,
    packagePrice: str,
    deliveryOption: str,
    custname: str,
    custaddress: str,
    customerDistrict: str,
    custPhone: str,

    pickMerchantName: str = "",
    pickMerchantAddress: str = "",
    pickMerchantThana: str = "",
    pickMerchantDistrict: str = "",
    pickupMerchantPhone: str = "",
    productBrief: str = "",
    max_weight: str = "",
):




    # Validate allowed values
    if productSizeWeight not in ["standard","large","special"]:
        return {
            "success": False,
            "message": "Invalid productSizeWeight",
            "allowed_values": ["standard","large","special"]
        }

    if deliveryOption not in ["regular","express"]:
        return {
            "success": False,
            "message": "Invalid deliveryOption",
            "allowed_values": ["regular","express"]
        }



    headers = {
        "Content-Type": "application/json",
        "Paperflykey": settings.PAPERFLY_KEY
    }

    try:
        response = requests.post(
            settings.PAPERFLY_ORDER_URL,
            json=payload,
            headers=headers,
            auth=HTTPBasicAuth(settings.PAPERFLY_USERNAME, settings.PAPERFLY_PASSWORD),
            timeout=30
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "message": "Paperfly API not reachable",
            "error": str(e)
        }

    try:
        result = response.json()

        tracking_number = None
        if result.get("success"):
            tracking_number = result["success"].get("tracking_number")

        # Save order to DB
        PaperflyOrder.objects.create(
            merchantCode=merchantCode,
            merOrderRef=merOrderRef,
            tracking_number=tracking_number,
            pickMerchantName=pickMerchantName,
            pickMerchantAddress=pickMerchantAddress,
            pickMerchantThana=pickMerchantThana,
            pickMerchantDistrict=pickMerchantDistrict,
            pickupMerchantPhone=pickupMerchantPhone,
            productSizeWeight=productSizeWeight,
            productBrief=productBrief,
            packagePrice=packagePrice,
            deliveryOption=deliveryOption,
            custname=custname,
            custaddress=custaddress,
            customerDistrict=customerDistrict,
            custPhone=custPhone,
            max_weight=max_weight,
        )

        return {
            "success": True,
            "data": result
        }

    except ValueError:
        return {
            "success": False,
            "message": "Invalid response from Paperfly"
        }