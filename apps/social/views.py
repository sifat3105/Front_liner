from django.conf import settings
from utils.base_view import BaseAPIView as APIView
from rest_framework.response import Response
from rest_framework import status, permissions
import requests
from .models import SocialAccount, FacebookPage
from .serializers import SocialAccountSerializer, FacebookPageSerializer
from apps.chat.utils import handle_message, send_message

class FacebookConnectURL(APIView):
    permission_classes = []

    def get(self, request):
        url = (
            "https://www.facebook.com/v19.0/dialog/oauth"
            f"?client_id={settings.FACEBOOK_APP_ID}"
            f"&redirect_uri={settings.FACEBOOK_REDIRECT_URI}"
            "&scope="
            "pages_show_list,"
            "pages_manage_posts,"
            "pages_read_engagement,"
            "pages_messaging,"
            "instagram_basic,"
            "instagram_content_publish"
        )
        return self.success(
            message="Facebook connect URL generated successfully",
            status_code=status.HTTP_200_OK,
            data={"url": url},
            meta={"action": "facebook_connect_url"}
        )
    


class FacebookCallback(APIView):
    permission_classes = []
    
    def get(self, request):

        code = request.GET.get("code")
        if not code:
            print("Code missing")
            return Response({"error": "Code missing"}, status=400)

        # 1️⃣ Exchange code for token
        token_url = "https://graph.facebook.com/v19.0/oauth/access_token"
        token_res = requests.get(token_url, params={
            "client_id": settings.FACEBOOK_APP_ID,
            "client_secret": settings.FACEBOOK_APP_SECRET,
            "redirect_uri": settings.FACEBOOK_REDIRECT_URI,
            "code": code,
        }).json()

        user_token = token_res.get("access_token")
        # user_token = "EAAtQDyOOeL0BQHadcaZCix0AH4eC6ZBfGB73hZAtQ6OR9zcNqNZCIpx5kd9MXVulZClusAo1k9CeoLZCHW0CIAZBzHxH5gLGIne9aoxQdSZBeSdYqozktbC1kBZBFKGVsxTgLve4TWIMQTd7yQ4gTPsZBomOpUPh3H10FbzZAsEe3oMjhwt6vZBZBcgVIt9yZAx7ucPYVebgWDsDZA9VUrmmdPXZCp0JZBXeEXuL0CD6vMUP30QNnM8KQgfjulJknGL8gaOFedMtcmifd7zS7e53Kh48coB7MwBz7sjsWhmN3ruGGhlUZD"

        # 2️⃣ Get FB user ID
        me = requests.get(
            "https://graph.facebook.com/me",
            params={"access_token": user_token}
        ).json()

        # 3️⃣ Save social account
        social, _ = SocialAccount.objects.update_or_create(
            user_id=1,
            platform="facebook",
            defaults={
                "user_access_token": user_token,
                "fb_user_id": me["id"]
            }
        )

        # 4️⃣ Fetch pages
        pages = requests.get(
            "https://graph.facebook.com/v19.0/me/accounts",
            params={"access_token": user_token}
        ).json()

        for p in pages.get("data", []):
            FacebookPage.objects.update_or_create(
                user_id=1,
                social_account=social,
                page_id=p["id"],
                defaults={
                    "page_name": p["name"],
                    "page_access_token": p["access_token"],
                    "category": p["category"],
                    "category_list": p["category_list"],
                    "tasks": p["tasks"],
                }
            )

        return self.success(
            message="Facebook pages connected successfully",
            status_code=status.HTTP_200_OK,
            data={},
            meta={"action": "facebook_connect"}
        )
    

class FacebookPageListView(APIView):
    permission_classes = []

    def get(self, request):
        social = (
            SocialAccount.objects
            .prefetch_related("facebook_pages")
            .get(user=request.user, platform="facebook")
        )

        pages = social.facebook_pages.all()
        data = FacebookPageSerializer(pages, many=True).data

        return self.success(
            message="Facebook pages fetched successfully",
            status_code=status.HTTP_200_OK,
            data=data,
            meta={"action": "facebook_pages"}
        )
    

def subscribe_page_to_messages(page_id, page_access_token):
    url = f"https://graph.facebook.com/v19.0/{page_id}/subscribed_apps"
    params = {
        "subscribed_fields": "messages,messaging_postbacks",
        "access_token": page_access_token
    }
    return requests.post(url, params=params).json()


class FacebookWebhook(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        print(request.GET.get("hub.verify_token"))
        if request.GET.get("hub.verify_token") == "my_fb_verify_token_2025":
            return Response(int(request.GET.get("hub.challenge")))
        return Response("Invalid token", status=403)
    
    def post(self, request):
        data = request.data
        # print(data)

        for entry in data.get("entry", []):
            for event in entry.get("messaging", []):
                sender_id = event["sender"]["id"]
                page_id = entry["id"]
                print(sender_id)
                print(page_id)

                if "message" in event:
                    text = event["message"].get("text", "")
                    print(text)
                    handle_message(page_id, sender_id, text)

        return Response("EVENT_RECEIVED")

# def send_message(page_access_token, recipient_id, text):
#     url = "https://graph.facebook.com/v19.0/me/messages"
#     payload = {
#         "recipient": {"id": recipient_id},
#         "message": {"text": text}
#     }
#     params = {"access_token": page_access_token}

#     return requests.post(url, json=payload, params=params).json()

# def get_page_token_from_db(page_id):
#     page = FacebookPage.objects.get(page_id=page_id)
#     return page.page_access_token


# def handle_message(page_id, sender_id, text):
#     page_token = get_page_token_from_db(page_id)

#     text = text.lower()

#     if "price" in text:
#         reply = "Please tell us which product you are interested in 💰"
#     elif "hello" in text or "hi" in text:
#         reply = "Hi 👋 How can we help you today?"
#     elif "order" in text:
#         reply = "Sure! Please share your order number 📦"
#     else:
#         reply = "Thanks for messaging us! A team member will reply shortly 😊"
#     print("result =============================================")
#     print(send_message(page_token, sender_id, reply))
    
    
def send_quick_replies(page_access_token, recipient_id):
    payload = {
        "recipient": {"id": recipient_id},
        "message": {
            "text": "How can we help you?",
            "quick_replies": [
                {"content_type": "text", "title": "Product Price", "payload": "PRICE"},
                {"content_type": "text", "title": "Order Status", "payload": "ORDER"},
                {"content_type": "text", "title": "Talk to Agent", "payload": "AGENT"}
            ]
        }
    }

    url = "https://graph.facebook.com/v19.0/me/messages"
    params = {"access_token": page_access_token}
    requests.post(url, json=payload, params=params)
    
    
class MessangerConnectWithBot(APIView):
    permission_classes = []
    
    def post(self, request):
        data = request.data
        
        p_id = data.get("page_id")
        page = FacebookPage.objects.get(id=p_id)
        
        response = subscribe_page_to_messages(page.page_id, page.page_access_token)
        print(response)
        return self.success(
            message="Successfully connected with bot",
            status_code=status.HTTP_200_OK,
            data={},
            meta={"action": "messanger_connect_with_bot"}
        )
        

