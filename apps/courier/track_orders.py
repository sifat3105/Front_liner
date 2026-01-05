from .models import CourierOrder, CourierOrderStatus
import os
from datetime import datetime


PAPERFLY_KEY=os.environ.get("PAPERFLY_KEY")
PAPERFLY_URL=os.environ.get("PAPERFLY_URL")
PAPERFLY_ORDER_URL=os.environ.get("PAPERFLY_ORDER_URL")
PAPERFLY_TRACK_URL=os.environ.get("PAPERFLY_TRACK_URL")
PAPERFLY_USERNAME=os.environ.get("PAPERFLY_USERNAME")
PAPERFLY_PASSWORD=os.environ.get("PAPERFLY_PASSWORD")
STEADFAST_BASE_URL = "https://portal.packzy.com/api/v1"
STEADFAST_API_KEY = "hqmvdgsdbe6n3jsnhqzqkvzx5ggdxxvu"
STEADFAST_SECRET_KEY = "rw476ldjejh3m7zvfbjnnkp7"



import requests
from requests.auth import HTTPBasicAuth

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

        response.raise_for_status()  # Raise error for 4xx/5xx
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


def track_paperfly_order(tracking_id, tracking_code):

    res = api_call_sync(
        method="post",
        url=PAPERFLY_TRACK_URL,
        body={
            "ReferenceNumber": tracking_id,
            "merchantCode": tracking_code
        },
        headers={
        "Content-Type": "application/json",
        "Paperflykey": PAPERFLY_KEY
        },
        auth=(PAPERFLY_USERNAME, PAPERFLY_PASSWORD),
        timeout=30
    )
    if res.get("success") or res.get("status_code") == 200:
        return res
    
def track_steadfast_order(tracking_id, tracking_code=None):
    return api_call_sync(
        method="get",
        url=f"{STEADFAST_BASE_URL}/status_by_cid/{tracking_id}",
        headers={
        "Api-Key": STEADFAST_API_KEY,
        "Secret-Key": STEADFAST_SECRET_KEY,
        "Authorization": f"Bearer {STEADFAST_API_KEY}",
        "Content-Type": "application/json"
    },
        timeout=30
    )
    
    
def track_other_order(tracking_id, tracking_code=None, url=None, method="post", headers=None, body=None, auth=None):
    res =  api_call_sync(
        method=method,
        url=url,
        headers=headers,
        body=body,
        auth=auth,
        timeout=30
    )
    if res.get("status_code") == 200:
        return res

def track_order(order_id):
    try:
        # Fetch the courier order
        courier_order = CourierOrder.objects.get(order__order_id=order_id)
    except CourierOrder.DoesNotExist:
        return None
    courier_name = courier_order.courier.name.lower()
    tracking_id = courier_order.tracking_id
    tracking_code = courier_order.tracking_code
    
    res = None 
    if courier_name == "paperfly":
        res = track_paperfly_order(tracking_id, tracking_code)
    elif courier_name == "steadfast":
        res = track_steadfast_order(tracking_id, tracking_code)  
    else:
        url = os.environ.get(f"{courier_name.upper()}_TRACK_URL")
        headers = None
        body = None

        suffix = os.environ.get(f"{courier_name.upper()}_SUFFIX")
        if suffix:
            url = f"{url}{suffix}"

        header_val = os.environ.get(f"{courier_name.upper()}_HEADER")
        if header_val:
            headers = {"Authorization": header_val}

        res = track_other_order(tracking_id, tracking_code, url=url, headers=headers, body=body)
        
    if not res or not isinstance(res, dict):
        res = {"delivery_status": None, "delivery_time": None}


    status_str = res.get("delivery_status")
    delivery_time = res.get("delivery_time") or datetime.now()
    if status_str:
        CourierOrderStatus.objects.get_or_create(
            courier_order=courier_order,
            status=status_str,
            defaults={"status_time": delivery_time}
        )
        
    return CourierOrder.objects.get(order__order_id=order_id)
    
    