from django.conf import settings
import requests

def get_long_lived_token(short_token):
    url = "https://graph.facebook.com/v19.0/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": settings.FACEBOOK_APP_ID,
        "client_secret": settings.FACEBOOK_APP_SECRET,
        "fb_exchange_token": short_token,
    }
    res = requests.get(url, params=params)
    data = res.json()
    return data.get("access_token") 