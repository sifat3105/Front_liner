import requests
from django.conf import settings
import logging
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

class CourierServiceError(Exception):
    pass

def create_courier_MO(courier,user,customer_name: str,customer_phone: str,delivery_address: str,weight: float = 1.0,note: str = "",):

    try:
        profile = user.userprofile
    except Exception:
        raise CourierServiceError("User profile not found")

    headers = {
        "Authorization": f"Bearer {courier.api_key}",
        "Content-Type": "application/json",
    }

    session = requests.Session()
    session.headers.update(headers)

    # Merchant Create
    try:
        merchant_response = session.post(
            url=courier.merchant_create_url,
            json={
                "name": user.get_full_name() or user.username,
                "email": user.email,
                "phone": profile.phone,
                "address": profile.address,
            },
            timeout=30,
        )
        merchant_response.raise_for_status()
    except RequestException as e:
        logger.error(f"Courier merchant create error: {e}")
        raise CourierServiceError("Courier merchant create failed")

    merchant_data = merchant_response.json()
    merchant_id = merchant_data.get("merchant_id")

    if not merchant_id:
        raise CourierServiceError("Courier merchant_id not found")

    # Order Create
    try:
        order_response = session.post(
            url=courier.order_create_url,
            json={
                "merchant_id": merchant_id,
                "customer_name": customer_name,
                "customer_phone": customer_phone,
                "delivery_address": delivery_address,
                "weight": weight,
                "note": note,
            },
            timeout=30,
        )
        order_response.raise_for_status()
    except RequestException as e:
        logger.error(f"Courier order create error: {e}")
        raise CourierServiceError("Courier order create failed")

    return {
        "success": True,
        "merchant_id": merchant_id,
        "data": order_response.json(),
    }



def create_courier_order(user_profile, courier_urls, customer_name, customer_phone, delivery_address, amount):

    headers = {
        "Authorization": f"Bearer {courier_urls['api_key']}",
        "Content-Type": "application/json"
    }

    # Merchant create
    merchant_payload = {
        "name": user_profile['name'],
        "email": user_profile['email'],
        "phone": user_profile['phone'],
        "address": user_profile['address'],
    }

    merchant_resp = requests.post(courier_urls['merchant_create'], json=merchant_payload, headers=headers)
    merchant_data = merchant_resp.json()
    merchant_id = merchant_data.get("merchant_id")
    if not merchant_id:
        return {"success": False, "error": "Merchant create failed"}

    # Order create
    order_payload = {
        "merchant_id": merchant_id,
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "delivery_address": delivery_address,
        "amount": amount
    }

    order_resp = requests.post(courier_urls['order_create'], json=order_payload, headers=headers)
    order_data = order_resp.json()

    return {"success": True, "merchant_id": merchant_id, "order": order_data}
