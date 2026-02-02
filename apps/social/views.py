from django.conf import settings
from django.shortcuts import redirect
from utils.base_view import BaseAPIView as APIView
from rest_framework.response import Response
from rest_framework import status, permissions
import requests
from .models import SocialAccount, FacebookPage, SocialPlatform, InstagramAccount, WhatsAppBusinessAccount
from .serializers import SocialAccountSerializer, FacebookPageSerializer, SocialPlatformSerializer
import urllib.parse
import uuid
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .utils import get_long_lived_token, fetch_whatsapp_assets
from urllib.parse import urlencode, quote_plus
from django.http import HttpResponse
from datetime import datetime, timedelta
from .close_response import close_html_response
from .webhook_helper import dispatch_feed, dispatch_messaging


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
    permission_classes = [permissions.IsAuthenticated]

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
    PLATFORM_CONFIG = settings.PLATFORM_CONFIG

    def get(self, request, platform):
        user = request.user
        platform = platform.lower()

        config = self.PLATFORM_CONFIG.get(platform)
        if not config:
            return Response({"error": "Unsupported platform"}, status=400)

        state = str(uuid.uuid4())
        cache.set(
            f"{config['state_prefix']}{state}",
            user.id,
            timeout=300
        )

        if platform == "tiktok":
            params = {
                "client_key": config["client_id"],
                "response_type": "code",
                "scope": " ".join(config["scope"]),  # SPACE separated
                "redirect_uri": config["redirect_uri"],
                "state": state,
            }

            url = f"{config['auth_url']}?{urlencode(params, quote_via=quote_plus)}"

        else:
            params = {
                "client_id": config["client_id"],
                "response_type": "code",
                "scope": ",".join(config["scope"]),
                "redirect_uri": config["redirect_uri"],
                "state": state,
            }

            url = f"{config['auth_url']}?{urlencode(params)}"

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
        graph_access_token = long_lived_token or user_token

        me = requests.get(
            "https://graph.facebook.com/me",
            params={"access_token": graph_access_token}
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
            params={"access_token": graph_access_token}
        ).json()
        
        print("Facebook pages:", pages)

        for p in pages.get("data", []):
            FacebookPage.objects.update_or_create(
                user_id=user_id,
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
    
        

        return close_html_response('facebook', status='success')
        
        
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


        return close_html_response('instagram', status='success')
        
        
class WhatsappCallback(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):

        access_token = request.data.get("access_token")
        user = request.user

        if not access_token:
            return self.error(
                message="Missing access_token",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        result = []

        businesses_resp = requests.get(
            "https://graph.facebook.com/v19.0/me/businesses",
            params={"access_token": access_token}
        )
        businesses_data = businesses_resp.json()
        businesses = businesses_data.get("data", [])

        if not businesses:
            return Response({
                "error": "No businesses found or token lacks business_management permission",
                "meta": businesses_data
            }, status=400)

        for biz in businesses:
            business_id = biz.get("id")
            business_name = biz.get("name")

            waba_resp = requests.get(
                f"https://graph.facebook.com/v19.0/{business_id}/owned_whatsapp_business_accounts",
                params={"access_token": access_token}
            )
            waba_data = waba_resp.json()
            wabas = waba_data.get("data", [])

            if not wabas:
                continue

            for waba in wabas:
                waba_id = waba.get("id")
                waba_name = waba.get("name")

                phones_resp = requests.get(
                    f"https://graph.facebook.com/v19.0/{waba_id}/phone_numbers",
                    params={"access_token": access_token}
                )
                phones_data = phones_resp.json()
                phones = phones_data.get("data", [])

                # 4️⃣ Save to DB (or update if exists)
                for phone in phones:
                    WhatsAppBusinessAccount.objects.update_or_create(
                        user=user,
                        waba_id=waba_id,
                        phone_number_id=phone.get("id"),
                        defaults={
                            "business_id": business_id,
                            "business_name": business_name,
                            "waba_name": waba_name,
                            "display_phone_number": phone.get("display_phone_number"),
                        }
                    )

                result.append({
                    "business_id": business_id,
                    "business_name": business_name,
                    "waba_id": waba_id,
                    "waba_name": waba_name,
                    "phone_numbers": phones,
                })

        if not result:
            return Response({
                "error": "No WhatsApp Business Accounts found. Make sure you are admin of a Business that owns WhatsApp.",
            }, status=400)
        print(result)
        return Response({
            "status": "success",
            "accounts": result
        })
        
        
class TikTokCallback(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        code = request.GET.get("code")
        state = request.GET.get("state")

        if not code or not state:
            return Response({"error": "Missing code or state"}, status=400)

        # Validate state
        cache_key = f"tiktok_oauth_{state}"
        user_id = cache.get(cache_key)
        if not user_id:
            return Response({"error": "Invalid or expired state"}, status=400)

        cache.delete(cache_key)

        # 🔁 Exchange code for access token
        token_url = "https://open.tiktokapis.com/v2/oauth/token/"

        payload = {
            "client_key": settings.TIKTOK_CLIENT_KEY,
            "client_secret": settings.TIKTOK_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.TIKTOK_REDIRECT_URI,
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        response = requests.post(token_url, data=payload, headers=headers)
        token_data = response.json()

        if response.status_code != 200:
            return Response({
                "error": "Failed to get access token",
                "details": token_data
            }, status=400)

        access_token = token_data["access_token"]
        refresh_token = token_data.get("refresh_token")        
        expires_in_seconds = token_data.get("expires_in")  
        access_token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in_seconds)
        

        SocialAccount.objects.update_or_create(
            user_id=user_id,
            platform="tiktok",
            defaults={
                "user_access_token": access_token,
                "long_lived_token": access_token,
                "token_expires_at": access_token_expires_at,
                "refresh_token": refresh_token,
                "refresh_expires_at": access_token_expires_at,
                "access_token_expires_at": access_token_expires_at,
            }
        )

        return close_html_response('tiktok', status='success')

    

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
        "subscribed_fields": "messages,messaging_postbacks,feed",
        "access_token": page_access_token
    }
    return requests.post(url, params=params).json()


class FacebookWebhook(APIView):
    authentication_classes = []
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
        try:
            for entry in data.get("entry", []):
                page_id = entry.get("id")

                for change in entry.get("changes", []):
                    field = change.get("field")
                    if field == "feed":
                        dispatch_feed(page_id, change)

                for event in entry.get("messaging", []):
                    dispatch_messaging(page_id, event)

        except Exception:
            return Response("EVENT_RECEIVED", status=status.HTTP_200_OK)

        return Response("EVENT_RECEIVED", status=status.HTTP_200_OK)
    
    
class InstagramWebhook(APIView):
    authentication_classes = []
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
