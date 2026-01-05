from .models import CourierOrder
import os
import httpx

PAPERFLY_KEY=os.environ.get("PAPERFLY_KEY")
PAPERFLY_URL=os.environ.get("PAPERFLY_URL")
PAPERFLY_ORDER_URL=os.environ.get("PAPERFLY_ORDER_URL")
PAPERFLY_TRACK_URL=os.environ.get("PAPERFLY_TRACK_URL")
PAPERFLY_USERNAME=os.environ.get("PAPERFLY_USERNAME")
PAPERFLY_PASSWORD=os.environ.get("PAPERFLY_PASSWORD")
STEADFAST_BASE_URL = "https://portal.packzy.com/api/v1"
STEADFAST_API_KEY = "hqmvdgsdbe6n3jsnhqzqkvzx5ggdxxvu"
STEADFAST_SECRET_KEY = "rw476ldjejh3m7zvfbjnnkp7"



async def api_call_async(**kwargs):
    async with httpx.AsyncClient(timeout=kwargs.get("timeout", 30)) as client:
        response = await client.request(
            method=kwargs["method"],
            url=kwargs["url"],
            headers=kwargs.get("headers"),
            params=kwargs.get("params"),
            json=kwargs.get("body"),
            auth=kwargs.get("auth"),
        )

    response.raise_for_status()
    return response.json()


async def track_paperfly_order(tracking_id, tracking_code):

    res = await api_call_async(
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
    
async def track_steadfast_order(tracking_id, tracking_code=None):
    res = await api_call_async(
        method="post",
        url=f"{STEADFAST_BASE_URL}/status_by_cid/{tracking_id}",
        headers={
        "Api-Key": STEADFAST_API_KEY,
        "Secret-Key": STEADFAST_SECRET_KEY,
        "Authorization": f"Bearer {STEADFAST_API_KEY}",
        "Content-Type": "application/json"
    },
        timeout=30
    )
    if res.get("status_code") == 200 and res.get("delivery_status"):
        return res
    else:
        return None
    
async def track_other_order(tracking_id, tracking_code=None, url=None, method="post", headers=None, body=None, auth=None):
    res = await api_call_async(
        method=method,
        url=url,
        headers=headers,
        body=body,
        auth=auth,
        timeout=30
    )
    if res.get("status_code") == 200:
        return res

    
async def track_order(order_id):
    courier_order = CourierOrder.objects.get(order_id=order_id)
    courier_name = courier_order.courier.name.lower()
    tracking_id = courier_order.tracking_id
    tracking_code = courier_order.tracking_code

    if courier_name == "paperfly":
        res = await track_paperfly_order(tracking_id, tracking_code)
        print(res)
    elif courier_name == "steadfast":
        res = await track_steadfast_order(tracking_id, tracking_code)
        print(res)
    else:
        url = f'{os.environ.get(f'{courier_name.upper()}_TRACK_URL')}'
        if os.environ.get(f'{courier_name.upper()}_SUFFIX'):
            url = f'{url}{os.environ.get(f"{courier_name.upper()}/SUFFIX")}'
            header = f'{os.environ.get(f"{courier_name.upper()}/HEADER")}'
        res = await track_other_order(tracking_id, tracking_code, url=url)
        
    return res
    
    