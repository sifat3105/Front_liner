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



def fetch_whatsapp_assets(access_token):
    result = []

    # 1. Businesses
    businesses = requests.get(
        "https://graph.facebook.com/v19.0/me/businesses",
        params={"access_token": access_token}
    ).json()
    for biz in businesses.get("data", []):
        biz_id = biz["id"]
        print(biz_id)
        print(biz.get("name"))
        print(biz.get("phone_number"))

        # 2. WABA
        wabas = requests.get(
            f"https://graph.facebook.com/v19.0/{biz_id}/whatsapp_business_accounts",
            params=
            {"access_token": access_token}
        ).json()
        print(wabas)

        for waba in wabas.get("data", []):
            waba_id = waba["id"]

            # 3. Phone Numbers
            phones = requests.get(
                f"https://graph.facebook.com/v19.0/{waba_id}/phone_numbers",
                params={"access_token": access_token}
            ).json()
            print(phones)

            result.append({
                "business_id": biz_id,
                "business_name": biz.get("name"),
                "waba_id": waba_id,
                "phone_numbers": phones.get("data", [])
            })

    return result
