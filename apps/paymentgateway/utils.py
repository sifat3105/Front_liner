import requests
from django.conf import settings


def create_shurjopay_payment(
    amount: float,
    order_id: str,
    customer_name: str,
    customer_address: str,
    customer_email: str,
    customer_phone: str,
    customer_city: str,

    customer_post_code: str = "",
    client_ip: str = "",
    discount_amount: float = 0.0,
    disc_percent: float = 0.0,
    customer_state: str = "",
    customer_country: str = "Bangladesh",
    shipping_address: str = "",
    shipping_city: str = "",
    shipping_country: str = "Bangladesh",
    received_person_name: str = "",
    shipping_phone_number: str = "",
    value1: str = "",
    value2: str = "",
    value3: str = "",
    value4: str = "",
):
    """
    Create a payment request to ShurjoPay gateway.
    """

    try:
        
        token_response = requests.post(
            url=f"{settings.SP_BASE_URL}/api/get_token",
            data={
                "username": settings.SP_USERNAME,
                "password": settings.SP_PASSWORD,
            },
            timeout=30,
        )
        token_response.raise_for_status()

        token_data = token_response.json()

        token = token_data["token"]
        store_id = token_data["store_id"]
        execute_url = token_data["execute_url"]

        # 2️⃣ Execute Payment
        payment_response = requests.post(
            url=execute_url,
            headers={
                "Authorization": f"Bearer {token}",
            },
            data={
                "prefix": settings.SP_PREFIX,
                "token": token,
                "return_url": settings.SP_RETURN_URL,
                "cancel_url": settings.SP_CANCEL_URL,
                "store_id": store_id,
                "amount": amount,
                "order_id": order_id,
                "currency": "BDT",

                "customer_name": customer_name,
                "customer_address": customer_address,
                "customer_email": customer_email,
                "customer_phone": customer_phone,
                "customer_city": customer_city,
                "customer_post_code": customer_post_code,
                "client_ip": client_ip,

                "discount_amount": discount_amount,
                "disc_percent": disc_percent,

                "customer_state": customer_state,
                "customer_country": customer_country,

                "shipping_address": shipping_address,
                "shipping_city": shipping_city,
                "shipping_country": shipping_country,

                "received_person_name": received_person_name,
                "shipping_phone_number": shipping_phone_number,

                "value1": value1,
                "value2": value2,
                "value3": value3,
                "value4": value4,
            },
            timeout=30,
        )

        payment_response.raise_for_status()

        return {
            "success": True,
            "data": payment_response.json(),
        }

    except requests.RequestException as e:
        return {
            "success": False,
            "error": str(e),
        }
