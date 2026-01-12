import requests
from django.conf import settings

def send_whatsapp_message(phone_number_id, message_text):
    """
    Send message to a WhatsApp user via Meta Graph API using System User token
    """

    url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"

    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_SYSTEM_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number_id,  # can be the WhatsApp number ID
        "type": "text",
        "text": {"body": message_text}
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.json()

SYSTEM_USER_TOKEN = "EAAtQDyOOeL0BQZALcxxX3D8x6vzEA7GktBYlhB0KaNoE2aeD2TW6Y3aMKZChe2aZC9ZAZB8uGUaShic79soG4iSvdb2nF0gGpXtgT9PQ82x2hjAxsqKovmY4OZCKkFwtr0LZB743Wgz783K4toUwUGVUPZA8OvoZAudkjBTN9bLVbmVRVUtXZBPeOm3YwrmvPLWTZCxawZDZD"

  # WABA phone_number_id


def send_whatsapp_text(phone_number_id, to_number, message):
    url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_number,
        "type": "text",
        "text": {"body": message}
    }

    headers = {
        "Authorization": f"Bearer {SYSTEM_USER_TOKEN}",
        "Content-Type": "application/json"
    }

    resp = requests.post(url, json=payload, headers=headers)
    return resp.json()
