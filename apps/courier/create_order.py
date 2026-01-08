from .models import CourierOrder
import os
import requests
from requests.auth import HTTPBasicAuth

PAPERFLY_KEY=os.environ.get("PAPERFLY_KEY")
PAPERFLY_URL=os.environ.get("PAPERFLY_URL")
PAPERFLY_ORDER_URL=os.environ.get("PAPERFLY_ORDER_URL")
PAPERFLY_TRACK_URL=os.environ.get("PAPERFLY_TRACK_URL")
PAPERFLY_USERNAME=os.environ.get("PAPERFLY_USERNAME")
PAPERFLY_PASSWORD=os.environ.get("PAPERFLY_PASSWORD")
STEADFAST_BASE_URL = "https://portal.packzy.com/api/v1"
STEADFAST_API_KEY = "hqmvdgsdbe6n3jsnhqzqkvzx5ggdxxvu"
STEADFAST_SECRET_KEY = "rw476ldjejh3m7zvfbjnnkp7"


def api_call_sync(**kwargs):
    try:
        response = requests.request(
            method=kwargs["method"].upper(),
            url=kwargs["url"],
            headers=kwargs.get("headers"),
            params=kwargs.get("params"),
            json=kwargs.get("body"),
            auth=kwargs.get("auth"),
            timeout=kwargs.get("timeout", 30)
        )

        response.raise_for_status()
        try:
            return response.json()
        except ValueError:
            return {"raw": response.text}

    except requests.Timeout:
        raise Exception("API request timed out")

    except requests.HTTPError as e:
        raise Exception(f"HTTP Error {response.status_code}: {response.text}")

    except Exception as e:
        raise Exception(f"Unknown error: {str(e)}")
    
    
def create_courier_paperfly_order(**kwargs):
    try:
        res = api_call_sync(
            method="post",
            url=PAPERFLY_ORDER_URL,
            body={
                "merchantCode": kwargs.get("merchantCode"),
                "merOrderRef": kwargs.get("merOrderRef"),
                "pickMerchantName": kwargs.get("pickMerchantName"),
                "pickMerchantAddress": kwargs.get("pickMerchantAddress"),
                "pickMerchantThana": kwargs.get("pickMerchantThana"),
                "pickMerchantDistrict": kwargs.get("pickMerchantDistrict"),
                "pickupMerchantPhone": kwargs.get("pickupMerchantPhone"),
                "productSizeWeight": kwargs.get("productSizeWeight"),
                "deliveryOption": kwargs.get("deliveryOption"),
                "custname": kwargs.get("custname"),
                "custaddress": kwargs.get("custaddress"),
                "customerThana": kwargs.get("customerThana"),
                "customerDistrict": kwargs.get("customerDistrict"),
                "custPhone": kwargs.get("custPhone"),
                "max_weight": kwargs.get("max_weight"),
            },
            headers={
            "Content-Type": "application/json",
            "Paperflykey": PAPERFLY_KEY
            },
            auth=HTTPBasicAuth(PAPERFLY_USERNAME, PAPERFLY_PASSWORD),
            timeout=30
        )
        if res.get("success") or res.get("status_code") == 200:
            return res
        
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "message": "Paperfly API not reachable",
            "error": str(e)
        }

