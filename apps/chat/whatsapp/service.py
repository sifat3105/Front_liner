import requests
from django.conf import settings


REQUEST_TIMEOUT = 10


def _resolve_token(access_token=None):
    return access_token or getattr(settings, "WHATSAPP_SYSTEM_TOKEN", "")


def send_whatsapp_message(phone_number_id, message_text, to_number=None, access_token=None):
    """
    Backward-compatible helper for sending plain text over WhatsApp.
    """
    target_number = to_number or phone_number_id
    return send_whatsapp_text(
        phone_number_id=phone_number_id,
        to_number=target_number,
        message=message_text,
        access_token=access_token,
    )


def send_whatsapp_text(phone_number_id, to_number, message, access_token=None):
    url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_number,
        "type": "text",
        "text": {"body": message}
    }

    headers = {
        "Authorization": f"Bearer {_resolve_token(access_token)}",
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=REQUEST_TIMEOUT)
        return resp.json()
    except requests.RequestException as exc:
        return {"error": {"message": str(exc)}}
