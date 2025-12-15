from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import requests
from .models import SocialAccount, FacebookPage

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
        # user_token = "EAAtQDyOOeL0BQN3RIml6PAaIvEZCBfW4Q8UxjaSNjE6ZCB86ENQABsEVSWwuxvUlZAdBVUZCt9gVb4cOfZC6ZCLVGDoeRjGCPlPDJZBNvHdt1WyRbeiYRJYZBPZAV0ZAQZCP5s6eTHZCsxRDKiOskd2oZA8q721GhUtWJ6RPPKCm4XigsZCMcobpZBiuMq1OwnReQcivYKZCgyEuMgAhrojg7a69uf2WDgLERrpi80oe2BMD0gB0Gfet0QPFtYz1OQB2mBrxq5fKHQNJHE2HiVHpZBOMhVLFB3ZAKo"

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
                    "page_access_token": p["access_token"]
                }
            )

        return Response({"message": "Facebook pages connected successfully"})
    

class FacebookPageListView(APIView):
    permission_classes = []

    def get(self, request):
        social = SocialAccount.objects.get(user=request.user, platform="facebook")
        user_access_token = social.user_access_token
        print(user_access_token)
        url = f"https://graph.facebook.com/v19.0/me/accounts?access_token={user_access_token}"
        print(url)
        res = requests.get(url)
        return Response(res.json())
    

# class 