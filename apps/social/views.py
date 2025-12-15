from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

class FacebookConnectURL(APIView):
    permission_classes = []

    def get(self, request):
        url = (
            "https://www.facebook.com/v19.0/dialog/oauth"
            f"?client_id={settings.FACEBOOK_APP_ID}"
            f"&redirect_uri={settings.FACEBOOK_REDIRECT_URI}"
            "&scope=pages_show_list,pages_manage_posts,pages_read_engagement,instagram_basic"
        )
        return Response({"url": url})
    

import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import SocialAccount, FacebookPage

class FacebookCallback(APIView):
    permission_classes = []

    def get(self, request):
        code = request.GET.get("code")
        if not code:
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

        # 2️⃣ Get FB user ID
        me = requests.get(
            "https://graph.facebook.com/me",
            params={"access_token": user_token}
        ).json()

        # 3️⃣ Save social account
        social, _ = SocialAccount.objects.update_or_create(
            user=request.user,
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
                user=request.user,
                social_account=social,
                page_id=p["id"],
                defaults={
                    "page_name": p["name"],
                    "page_access_token": p["access_token"]
                }
            )

        return Response({"message": "Facebook pages connected successfully"})
