from django.conf import settings
from django.shortcuts import redirect
from utils.base_view import BaseAPIView as APIView
from rest_framework.response import Response
from rest_framework import status, permissions
import requests
from .models import SocialAccount, FacebookPage, SocialPlatform, InstagramAccount
from .serializers import SocialAccountSerializer, FacebookPageSerializer, SocialPlatformSerializer
from apps.chat.utils import handle_message, send_message
import urllib.parse
import uuid
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .utils import get_long_lived_token


@method_decorator(csrf_exempt, name='dispatch')
class MetaDataDeletionAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        data = request.data
        user_id = data.get("user_id")
        confirmation_code = data.get("confirmation_code")
        if not user_id or not confirmation_code:
            return Response({"error": "Invalid data"}, status=400)
        
        # TODO: Delete or anonymize user data in your database
        # Example:
        # User.objects.filter(instagram_id=user_id).delete()

        # Return confirmation code to Facebook/Instagram
        return Response({
            "url": f"{request.build_absolute_uri()}/meta_data_deletion/",
            "confirmation_code": confirmation_code
        })



class SocialPlatformListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        platforms = SocialPlatform.objects.all()
        serializer = SocialPlatformSerializer(platforms, many=True, context={'request': request})
        return self.success(
            message="Social platforms fetched successfully",
            status_code=status.HTTP_200_OK,
            data=serializer.data,
            meta={"action": "social_platforms"}
        )

class SocialConnectURL(APIView):
    permission_classes = []
    PLATFORM_CONFIG =settings.PLATFORM_CONFIG
    
    def get(self, request, platform):
        user = request.user
        platform = platform.lower()

        config = self.PLATFORM_CONFIG.get(platform)
        if not config or not config.get("auth_url"):
            return Response(
                {"error": "Unsupported platform"},
                status=400
            )

        state = str(uuid.uuid4())
        cache.set(
            f"{config['state_prefix']}{state}",
            user.id,
            timeout=300
        )

        scope = ",".join(config["scope"])

        url = (
            f"{config['auth_url']}"
            f"?client_id={config['client_id']}"
            f"&redirect_uri={config['redirect_uri']}"
            f"&response_type=code"
            f"&state={state}"
            f"&scope={scope}"
            f"&force_reauth={config.get('force_reauth', False)}"
        )

        return Response({
            "status": "success",
            "message": f"{platform.capitalize()} connect URL generated successfully",
            "data": {
                "platform": platform,
                "url": url
            }
        })


class FacebookCallback(APIView):
    permission_classes = []
    
    def get(self, request):
        code = request.GET.get("code")
        state = request.GET.get("state")
        if not code:
            print("Code missing")
            return Response({"error": "Code missing"}, status=400)

        user_id = cache.get(f"facebook_oauth_{state}")
        if not user_id:
            return Response({"error": "Invalid or expired state"}, status=400)

        cache.delete(f"facebook_oauth_{state}")

        token_url = "https://graph.facebook.com/v19.0/oauth/access_token"
        token_res = requests.get(token_url, params={
            "client_id": settings.FACEBOOK_APP_ID,
            "client_secret": settings.FACEBOOK_APP_SECRET,
            "redirect_uri": settings.FACEBOOK_REDIRECT_URI,
            "code": code,
        }).json()

        user_token = token_res.get("access_token")
        long_lived_token = get_long_lived_token(user_token)

        me = requests.get(
            "https://graph.facebook.com/me",
            params={"access_token": user_token}
        ).json()
        print("Facebook user info:", me)

        social, _ = SocialAccount.objects.update_or_create(
            user_id=user_id,
            platform="facebook",
            defaults={
                "user_access_token": user_token,
                "long_lived_token": long_lived_token,
                "fb_user_id": me["id"],
                "name": me["name"],
            }
        )

        pages = requests.get(
            "https://graph.facebook.com/v19.0/me/accounts",
            params={"access_token": user_token}
        ).json()
        
        print("Facebook pages:", pages)

        for p in pages.get("data", []):
            long_lived_token = get_long_lived_token(p["access_token"])
            FacebookPage.objects.update_or_create(
                user_id=1,
                social_account=social,
                page_id=p["id"],
                defaults={
                    "page_name": p["name"],
                    "page_access_token": long_lived_token,
                    "category": p["category"],
                    "category_list": p["category_list"],
                    "tasks": p["tasks"],
                }
            )
    
        return redirect(
            "https://frontliner-dashboard.vercel.app/user/social/connect/fallback?platform=facebook&status=success"
        )
        
        
class InstagramCallback(APIView):
    permission_classes = []

    def get(self, request):
        code = request.GET.get("code")
        state = request.GET.get("state")

        if not code:
            return Response({"error": "Code missing"}, status=400)

        user_id = cache.get(f"instagram_oauth_{state}")
        if not user_id:
            return Response({"error": "Invalid or expired state"}, status=400)

        cache.delete(f"instagram_oauth_{state}")

        # 1️⃣ Exchange code for short-lived token
        token_res = requests.get(
            "https://graph.facebook.com/v19.0/oauth/access_token",
            params={
                "client_id": settings.FACEBOOK_APP_ID,
                "client_secret": settings.FACEBOOK_APP_SECRET,
                "redirect_uri": settings.INSTAGRAM_REDIRECT_URI,
                "code": code,
            }
        ).json()

        user_token = token_res.get("access_token")
        if not user_token:
            return Response({"error": "Failed to get access token"}, status=400)

        # 2️⃣ Long-lived token
        long_lived_token = get_long_lived_token(user_token)

        # 3️⃣ Save social account
        social, _ = SocialAccount.objects.update_or_create(
            user_id=user_id,
            platform="instagram",
            defaults={
                "user_access_token": user_token,
                "long_lived_token": long_lived_token,
            }
        )

        # 4️⃣ Get Facebook Pages
        pages = requests.get(
            "https://graph.facebook.com/v19.0/me/accounts",
            params={"access_token": user_token}
        ).json()

        for page in pages.get("data", []):
            page_token = page["access_token"]

            ig_res = requests.get(
                f"https://graph.facebook.com/v19.0/{page['id']}",
                params={
                    "fields": "instagram_business_account{name,username,profile_picture_url}",
                    "access_token": page_token,
                }
            ).json()

            ig = ig_res.get("instagram_business_account")
            if not ig:
                continue  
            InstagramAccount.objects.update_or_create(
                ig_user_id=ig["id"],
                defaults={
                    "user_id": user_id,
                    "social_account": social,
                    "username": ig.get("username"),
                    "name": ig.get("name"),
                    "profile_picture": ig.get("profile_picture_url"),
                    "page_id": page["id"],
                    "page_access_token": page_token,
                }
            )

        return redirect(
            "https://frontliner-dashboard.vercel.app/user/social/connect/fallback"
            "?platform=instagram&status=success"
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
        try:
            if request.GET.get("hub.verify_token") == settings.FB_VERIFY_TOKEN:
                return Response(int(request.GET.get("hub.challenge")))
        except Exception as e:
            print("Webhook verification error:", e)
        return Response("Invalid token", status=403)
    
    def post(self, request):
        data = request.data
        object = data.get("object")
        print(object)
        for entry in data.get("entry", []):
            for event in entry.get("messaging", []):
                sender_id = event["sender"]["id"]
                page_id = entry["id"]

                if "message" in event:
                    text = event["message"].get("text", "")
                    print(text)
                    handle_message(page_id, sender_id, text)

        return Response("EVENT_RECEIVED")
    
    
class InstagramWebhook(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        data = request.data
        
        for entry in data.get("entry", []):
            for event in entry.get("messaging", []):
                sender_id = event["sender"]["id"]
                page_id = entry["id"]
                
                if "message" in event:
                    text = event["message"].get("text", "")
                    print(text)
                    handle_message(page_id, sender_id, text)
                    
                    
        return Response("EVENT_RECEIVED")
    

    
class MessangerConnectWithBot(APIView):
    permission_classes = []
    
    def post(self, request):
        data = request.data
        
        p_id = data.get("page_id")
        platform = data.get("platform")
        if platform == "instagram":
            page = InstagramAccount.objects.get(id=p_id)
            print(page)
        else:
            page = FacebookPage.objects.get(id=p_id)
        
        response = subscribe_page_to_messages(page.page_id, page.page_access_token)
        print(response)
        return self.success(
            message="Successfully connected with bot",
            status_code=status.HTTP_200_OK,
            data={},
            meta={"action": "messanger_connect_with_bot"}
        )
        

        
class TikTokConnectURL(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        client_key = settings.TIKTOK_CLIENT_KEY
        redirect_uri = settings.TIKTOK_REDIRECT_URI  # don't quote yet
        redirect_uri_encoded = urllib.parse.quote(redirect_uri, safe='')  # encode safely

        scope = "user.info.basic,video.list"
        state = request.user.id if request.user.is_authenticated else "guest"

        url = (
            f"https://www.tiktok.com/auth/authorize/"
            f"?client_key={client_key}"
            f"&redirect_uri={redirect_uri_encoded}"
            f"&response_type=code"
            f"&scope={scope}"
            f"&state={state}"
        )

        return self.success(
            message="TikTok connect URL generated successfully",
            status_code=status.HTTP_200_OK,
            data={"url": url},
            meta={"action": "tiktok_connect_url"}
        )
        
class FacebookDeletion(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        data = request.data
        page_id = data.get("page_id")
        page = FacebookPage.objects.get(id=page_id)
        
        response = requests.delete(
            f"https://graph.facebook.com/v19.0/{page_id}",
            params={"access_token": page.page_access_token}
        )
        
        return self.success(
            message="Facebook page deleted successfully",
            status_code=response.status_code,
            meta={"action": "facebook_page_deleted"}
        )
