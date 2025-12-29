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

    data_dict = locals() 
    
    # Prepare payload for API
    payload = {k: v for k, v in data_dict.items()}

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


 

import requests
from django.conf import settings
from requests.auth import HTTPBasicAuth

from .models import PaperflyOrder, SteadfastOrder, PathaoOrder  

COURIER_MODELS = {
    "paperfly": PaperflyOrder,
    "stedfast": SteadfastOrder,
    "pathao": PathaoOrder,
}

COURIER_API_CONFIG = {
    "paperfly": {
        "url": settings.PAPERFLY_ORDER_URL,
        "auth": HTTPBasicAuth(settings.PAPERFLY_USERNAME, settings.PAPERFLY_PASSWORD),
        "headers": {"Content-Type": "application/json", "Paperflykey": settings.PAPERFLY_KEY}
    },
    "stedfast": {
        "url": settings.STEADFAST_ORDER_URL,
        "auth": None,
        "headers": {"Content-Type": "application/json", "Authorization": f"Bearer {settings.STEADFAST_KEY}"}
    },
    "pathao": {
        "url": settings.PATHAO_ORDER_URL,
        "auth": None,
        "headers": {"Content-Type": "application/json", "Authorization": f"Bearer {settings.PATHAO_KEY}"}
    }
}

def create_courier_order_generic(courier: str, payload: dict):

    courier = courier.lower()
    if courier not in COURIER_MODELS:
        return {"success": False, "message": f"Unsupported courier: {courier}"}

    model = COURIER_MODELS[courier]
    config = COURIER_API_CONFIG[courier]

    # Mandatory field validation
    mandatory_fields = ["merchantCode", "merOrderRef", "custname", "custaddress", "custPhone"]
    missing_fields = [f for f in mandatory_fields if not payload.get(f)]
    if missing_fields:
        return {
            "success": False,
            "message": "Missing mandatory fields",
            "missing_fields": missing_fields
        }

    # API call
    try:
        response = requests.post(
            url=config["url"],
            json=payload,
            headers=config["headers"],
            auth=config.get("auth"),
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"{courier} API not reachable", "error": str(e)}
    except ValueError:
        return {"success": False, "message": f"Invalid response from {courier}"}

    # Save to DB
    try:
        # For Paperfly: tracking_number
        tracking_number = result.get("success", {}).get("tracking_number") if courier == "paperfly" else None

        # Generic fields save
        model.objects.create(
            tracking_number=tracking_number if courier == "paperfly" else None,
            **{k: v for k, v in payload.items()}
        )
    except Exception as e:
        return {"success": False, "message": f"DB save error for {courier}", "error": str(e)}

    return {"success": True, "data": result}
