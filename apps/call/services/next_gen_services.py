import os
import httpx

NGS_BASE_URL = os.getenv("NGS_BASE_URL")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL")
NGS_AUTH_CODE = os.getenv("NGS_AUTH_CODE")
NGS_AUTH_SECRET = os.getenv("NGS_AUTH_SECRET")


def ngs_headers():
    return {
        "X-Authorization": NGS_AUTH_CODE,
        "X-Authorization-Secret": NGS_AUTH_SECRET,
        "Content-Type": "application/x-www-form-urlencoded",
    }

async def make_a_call(ngs_from: int, to: int, order_id: int):

        status_cb = f"{PUBLIC_BASE_URL}/api/call/webhooks/ngs/status"
        response_url = f"{PUBLIC_BASE_URL}/api/call/ngs/{order_id}/voice.xml"

        data = {
            "to": to,
            "from": ngs_from,
            "statusCallback": status_cb,
            "response": response_url,
        }

        call_create_url = f"{NGS_BASE_URL}/api/v1/call"

        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(call_create_url, headers=ngs_headers(), data=data)

        try:
            body = r.json()
        except Exception:
            body = {"text": r.text}
            
            
            
def get_xml(self, params : dict = None):
    
    ws_url = f"{PUBLIC_BASE_URL.replace('https://','wss://').replace('http://','ws://')}/ws/agent"
    xml = f"""<?xml version="1.0"?>
    <response>
    <connect>
        <stream name="stream" url="{ws_url}">
        <parameter name="bot" value="support-agent" />
        </stream>
    </connect>
    </response>
    """
    return xml