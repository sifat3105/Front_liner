import logging
import uuid
from datetime import timedelta
from urllib.parse import quote_plus, urlencode

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from requests import RequestException
from rest_framework import permissions, status
from rest_framework.response import Response
from utils.base_view import BaseAPIView as APIView

from .close_response import close_html_response
from .models import (
    FacebookPage,
    InstagramAccount,
    SocialAccount,
    SocialPlatform,
    WhatsAppBusinessAccount,
)
from .serializers import (
    FacebookPageSerializer,
    SocialPlatformSerializer,
    WhatsAppBusinessAccountSerializer,
)
from .utils import get_long_lived_token
from .webhook_helper import (
    dispatch_feed,
    dispatch_messaging,
    dispatch_tiktok_feed,
    dispatch_whatsapp_messages,
)

logger = logging.getLogger(__name__)
User = get_user_model()

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"
TIKTOK_TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
TIKTOK_PROFILE_URL = "https://open.tiktokapis.com/v2/user/info/"
REQUEST_TIMEOUT = 15


def _request_json(method, url, **kwargs):
    kwargs.setdefault("timeout", REQUEST_TIMEOUT)
    try:
        response = requests.request(method, url, **kwargs)
    except RequestException as exc:
        return None, {"error": {"message": str(exc)}}

    try:
        data = response.json()
    except ValueError:
        data = {"error": {"message": "Invalid JSON response"}}

    return response, data


def _resolve_user_id(state_prefix, state):
    if not state:
        return None
    cache_key = f"{state_prefix}{state}"
    user_id = cache.get(cache_key)
    if user_id:
        cache.delete(cache_key)
    return user_id


def _exchange_meta_code_for_token(code, redirect_uri=None):
    params = {
        "client_id": settings.FACEBOOK_APP_ID,
        "client_secret": settings.FACEBOOK_APP_SECRET,
        "code": code,
    }
    if redirect_uri:
        params["redirect_uri"] = redirect_uri

    _, token_data = _request_json(
        "GET",
        f"{GRAPH_API_BASE}/oauth/access_token",
        params=params,
    )
    return token_data


def _exchange_whatsapp_code_for_token(code):
    token_data = _exchange_meta_code_for_token(code, settings.WHATSAPP_REDIRECT_URI)
    if token_data.get("access_token"):
        return token_data

    fallback_token_data = _exchange_meta_code_for_token(code, redirect_uri=None)
    if fallback_token_data.get("access_token"):
        return fallback_token_data

    return fallback_token_data or token_data or {}


def _upsert_whatsapp_social_account(user, access_token):
    long_lived_token = get_long_lived_token(access_token) or access_token
    social, _ = SocialAccount.objects.update_or_create(
        user=user,
        platform="whatsapp",
        defaults={
            "user_access_token": access_token,
            "long_lived_token": long_lived_token,
            "name": "WhatsApp Business",
        },
    )
    graph_access_token = (
        social.long_lived_token
        or social.user_access_token
        or access_token
    )
    return social, graph_access_token


def _subscribe_whatsapp_waba(waba_id, access_token):
    _, data = _request_json(
        "POST",
        f"{GRAPH_API_BASE}/{waba_id}/subscribed_apps",
        params={"access_token": access_token},
    )
    return data


def _subscribe_synced_whatsapp_accounts(accounts, access_token):
    results = []
    seen_waba_ids = set()
    for account in accounts or []:
        waba_id = account.get("waba_id")
        if not waba_id or waba_id in seen_waba_ids:
            continue
        seen_waba_ids.add(waba_id)
        results.append(
            {
                "waba_id": waba_id,
                "subscription": _subscribe_whatsapp_waba(waba_id, access_token),
            }
        )
    return results


def _sync_whatsapp_accounts(user, access_token):
    _, businesses_data = _request_json(
        "GET",
        f"{GRAPH_API_BASE}/me/businesses",
        params={"access_token": access_token},
    )
    businesses = (businesses_data or {}).get("data", [])

    if not businesses:
        return [], (
            "No businesses found or token lacks required WhatsApp permissions."
        ), businesses_data

    result = []
    for biz in businesses:
        business_id = biz.get("id")
        if not business_id:
            continue
        business_name = biz.get("name") or ""

        _, waba_data = _request_json(
            "GET",
            f"{GRAPH_API_BASE}/{business_id}/owned_whatsapp_business_accounts",
            params={"access_token": access_token},
        )
        wabas = (waba_data or {}).get("data", [])
        if not wabas:
            continue

        for waba in wabas:
            waba_id = waba.get("id")
            if not waba_id:
                continue
            waba_name = waba.get("name") or ""

            _, phones_data = _request_json(
                "GET",
                f"{GRAPH_API_BASE}/{waba_id}/phone_numbers",
                params={"access_token": access_token},
            )
            phones = (phones_data or {}).get("data", [])

            for phone in phones:
                phone_id = phone.get("id")
                if not phone_id:
                    continue
                WhatsAppBusinessAccount.objects.update_or_create(
                    user=user,
                    waba_id=waba_id,
                    phone_number_id=phone_id,
                    defaults={
                        "business_id": business_id,
                        "business_name": business_name,
                        "waba_name": waba_name,
                        "display_phone_number": phone.get("display_phone_number", ""),
                    },
                )

            result.append(
                {
                    "business_id": business_id,
                    "business_name": business_name,
                    "waba_id": waba_id,
                    "waba_name": waba_name,
                    "phone_numbers": phones,
                }
            )

    if not result:
        return [], (
            "No WhatsApp Business Accounts found. Ensure this user is admin of a business that owns WhatsApp."
        ), None

    return result, None, None


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
        platforms = SocialPlatform.objects.filter(is_active=True).order_by("id")
        serializer = SocialPlatformSerializer(platforms, many=True, context={"request": request})
        return self.success(
            message="Social platforms fetched successfully",
            status_code=status.HTTP_200_OK,
            data=serializer.data,
            meta={"action": "social_platforms"}
        )


class SocialConnectURL(APIView):
    permission_classes = [permissions.IsAuthenticated]
    PLATFORM_CONFIG = settings.PLATFORM_CONFIG

    def get(self, request, platform):
        platform = platform.lower()
        config = self.PLATFORM_CONFIG.get(platform)
        if not config:
            return self.error(
                message="Unsupported platform",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        state = str(uuid.uuid4())
        cache.set(
            f"{config['state_prefix']}{state}",
            request.user.id,
            timeout=300
        )

        if platform == "tiktok":
            params = {
                "client_key": config["client_id"],
                "response_type": "code",
                "scope": ",".join(config["scope"]),
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

        return self.success(
            message=f"{platform.capitalize()} connect URL generated successfully",
            status_code=status.HTTP_200_OK,
            data={"platform": platform, "url": url},
            meta={"action": "social_connect_url"}
        )


class FacebookCallback(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        code = request.GET.get("code")
        state = request.GET.get("state")
        if not code or not state:
            return close_html_response("facebook", status="error", message="Missing code or state")

        user_id = _resolve_user_id("facebook_oauth_", state)
        if not user_id:
            return close_html_response("facebook", status="error", message="Invalid or expired state")

        token_res = _exchange_meta_code_for_token(code, settings.FACEBOOK_REDIRECT_URI)
        user_token = token_res.get("access_token")
        if not user_token:
            return close_html_response("facebook", status="error", message="Failed to get access token")

        long_lived_token = get_long_lived_token(user_token)
        graph_access_token = long_lived_token or user_token

        _, me = _request_json(
            "GET",
            f"{GRAPH_API_BASE}/me",
            params={"fields": "id,name", "access_token": graph_access_token},
        )
        if "error" in me:
            return close_html_response("facebook", status="error", message="Unable to fetch Facebook profile")

        social, _ = SocialAccount.objects.update_or_create(
            user_id=user_id,
            platform="facebook",
            defaults={
                "user_access_token": user_token,
                "long_lived_token": long_lived_token,
                "fb_user_id": me.get("id"),
                "name": me.get("name"),
            }
        )

        _, pages = _request_json(
            "GET",
            f"{GRAPH_API_BASE}/me/accounts",
            params={"access_token": graph_access_token},
        )

        active_page_ids = []
        for page in pages.get("data", []):
            page_id = page.get("id")
            if not page_id:
                continue
            active_page_ids.append(page_id)
            FacebookPage.objects.update_or_create(
                user_id=user_id,
                social_account=social,
                page_id=page_id,
                defaults={
                    "page_name": page.get("name", ""),
                    "page_access_token": page.get("access_token", ""),
                    "category": page.get("category"),
                    "category_list": page.get("category_list") or [],
                    "tasks": page.get("tasks") or [],
                    "is_active": True,
                }
            )
        if active_page_ids:
            FacebookPage.objects.filter(
                user_id=user_id, social_account=social
            ).exclude(page_id__in=active_page_ids).update(is_active=False)

        return close_html_response("facebook", status="success")


class InstagramCallback(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        code = request.GET.get("code")
        state = request.GET.get("state")
        if not code or not state:
            return close_html_response("instagram", status="error", message="Missing code or state")

        user_id = _resolve_user_id("instagram_oauth_", state)
        if not user_id:
            return close_html_response("instagram", status="error", message="Invalid or expired state")

        token_res = _exchange_meta_code_for_token(code, settings.INSTAGRAM_REDIRECT_URI)

        user_token = token_res.get("access_token")
        if not user_token:
            return close_html_response("instagram", status="error", message="Failed to get access token")

        long_lived_token = get_long_lived_token(user_token)
        graph_access_token = long_lived_token or user_token

        social, _ = SocialAccount.objects.update_or_create(
            user_id=user_id,
            platform="instagram",
            defaults={
                "user_access_token": user_token,
                "long_lived_token": long_lived_token,
            }
        )

        _, pages = _request_json(
            "GET",
            f"{GRAPH_API_BASE}/me/accounts",
            params={"access_token": graph_access_token},
        )

        active_ig_ids = []
        for page in pages.get("data", []):
            page_id = page.get("id")
            page_token = page.get("access_token")
            if not page_id or not page_token:
                continue

            _, ig_res = _request_json(
                "GET",
                f"{GRAPH_API_BASE}/{page_id}",
                params={
                    "fields": "instagram_business_account{id,name,username,profile_picture_url}",
                    "access_token": page_token,
                }
            )

            ig = ig_res.get("instagram_business_account")
            if not ig:
                continue
            ig_user_id = ig.get("id")
            if not ig_user_id:
                continue
            active_ig_ids.append(ig_user_id)
            InstagramAccount.objects.update_or_create(
                ig_user_id=ig_user_id,
                defaults={
                    "user_id": user_id,
                    "social_account": social,
                    "username": ig.get("username") or "",
                    "name": ig.get("name") or (ig.get("username") or ""),
                    "profile_picture": ig.get("profile_picture_url"),
                    "page_id": page_id,
                    "page_access_token": page_token,
                    "is_active": True,
                }
            )

        if active_ig_ids:
            InstagramAccount.objects.filter(
                user_id=user_id, social_account=social
            ).exclude(ig_user_id__in=active_ig_ids).update(is_active=False)

        return close_html_response("instagram", status="success")


class WhatsappCallback(APIView):
    permission_classes = [permissions.AllowAny]

    def _sync_for_user(self, user, access_token):
        _, graph_access_token = _upsert_whatsapp_social_account(user, access_token)
        accounts, error_message, meta = _sync_whatsapp_accounts(user, graph_access_token)
        if error_message:
            return None, error_message, meta, []
        subscriptions = _subscribe_synced_whatsapp_accounts(accounts, graph_access_token)
        return accounts, None, None, subscriptions

    def get(self, request):
        code = request.GET.get("code")
        state = request.GET.get("state")
        if not code or not state:
            return close_html_response("whatsapp", status="error", message="Missing code or state")

        user_id = _resolve_user_id("whatsapp_oauth_", state)
        if not user_id:
            return close_html_response("whatsapp", status="error", message="Invalid or expired state")

        user = User.objects.filter(id=user_id).first()
        if not user:
            return close_html_response("whatsapp", status="error", message="User not found")

        token_data = _exchange_whatsapp_code_for_token(code)
        access_token = token_data.get("access_token")
        if not access_token:
            return close_html_response("whatsapp", status="error", message="Failed to get access token")

        accounts, error_message, _, subscriptions = self._sync_for_user(user, access_token)
        if error_message:
            return close_html_response("whatsapp", status="error", message=error_message)
        logger.info(
            "WhatsApp accounts synced via OAuth: user=%s accounts=%s subscriptions=%s",
            user.id,
            len(accounts),
            len(subscriptions),
        )
        return close_html_response("whatsapp", status="success")

    def post(self, request):
        user = request.user if request.user and request.user.is_authenticated else None
        if not user:
            state = request.data.get("state")
            state_user_id = _resolve_user_id("whatsapp_oauth_", state)
            if state_user_id:
                user = User.objects.filter(id=state_user_id).first()
        if not user:
            return self.error(
                message="Authentication or valid state is required",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        code = request.data.get("code")
        access_token = request.data.get("access_token")
        if not access_token and code:
            token_data = _exchange_whatsapp_code_for_token(code)
            access_token = token_data.get("access_token")
        else:
            token_data = {}
        if not access_token:
            return self.error(
                message="Missing access_token or code",
                errors=(token_data or {}).get("error"),
                status_code=status.HTTP_400_BAD_REQUEST
            )

        result, error_message, meta, subscriptions = self._sync_for_user(user, access_token)
        if error_message:
            return self.error(
                message=error_message,
                data={"meta": meta} if meta else None,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return self.success(
            message="WhatsApp accounts synced successfully",
            status_code=status.HTTP_200_OK,
            data={
                "accounts": result,
                "subscriptions": subscriptions,
            },
            meta={"action": "whatsapp_accounts_synced"},
        )


class TikTokCallback(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        code = request.GET.get("code")
        state = request.GET.get("state")
        if not code or not state:
            return close_html_response("tiktok", status="error", message="Missing code or state")

        user_id = _resolve_user_id("tiktok_oauth_", state)
        if not user_id:
            return close_html_response("tiktok", status="error", message="Invalid or expired state")

        payload = {
            "client_key": settings.TIKTOK_CLIENT_KEY,
            "client_secret": settings.TIKTOK_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.TIKTOK_REDIRECT_URI,
        }

        response, token_data = _request_json(
            "POST",
            TIKTOK_TOKEN_URL,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if not response or response.status_code != 200:
            logger.warning("TikTok token exchange failed: %s", token_data)
            return close_html_response("tiktok", status="error", message="Failed to get access token")

        access_token = token_data.get("access_token")
        if not access_token:
            return close_html_response("tiktok", status="error", message="Access token missing")

        refresh_token = token_data.get("refresh_token")
        expires_in_seconds = int(token_data.get("expires_in") or 0)
        refresh_expires_in = int(token_data.get("refresh_expires_in") or expires_in_seconds or 0)
        access_token_expires_at = timezone.now() + timedelta(seconds=expires_in_seconds or 0)
        refresh_expires_at = timezone.now() + timedelta(seconds=refresh_expires_in)

        _, profile_data = _request_json(
            "GET",
            TIKTOK_PROFILE_URL,
            params={"fields": "open_id,display_name,avatar_url"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        profile_user = (profile_data or {}).get("data", {}).get("user", {})

        SocialAccount.objects.update_or_create(
            user_id=user_id,
            platform="tiktok",
            defaults={
                "user_access_token": access_token,
                "long_lived_token": access_token,
                "token_expires_at": access_token_expires_at,
                "refresh_token": refresh_token,
                "refresh_expires_at": refresh_expires_at,
                "access_token_expires_at": access_token_expires_at,
                "tk_user_id": profile_user.get("open_id"),
                "name": profile_user.get("display_name"),
            }
        )

        return close_html_response("tiktok", status="success")


class FacebookPageListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        social = (
            SocialAccount.objects
            .prefetch_related("facebook_pages")
            .filter(user=request.user, platform="facebook")
            .first()
        )
        if not social:
            return self.error(
                message="Facebook account not connected",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        pages = social.facebook_pages.filter(is_active=True)
        data = FacebookPageSerializer(pages, many=True).data

        return self.success(
            message="Facebook pages fetched successfully",
            status_code=status.HTTP_200_OK,
            data=data,
            meta={"action": "facebook_pages"}
        )


class WhatsAppBusinessAccountListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        accounts = (
            WhatsAppBusinessAccount.objects
            .filter(user=request.user)
            .order_by("-updated_at", "-id")
        )
        data = WhatsAppBusinessAccountSerializer(accounts, many=True).data
        return self.success(
            message="WhatsApp accounts fetched successfully",
            status_code=status.HTTP_200_OK,
            data=data,
            meta={"action": "whatsapp_accounts"},
        )


def subscribe_page_to_messages(page_id, page_access_token):
    url = f"{GRAPH_API_BASE}/{page_id}/subscribed_apps"
    params = {
        "subscribed_fields": "feed,messages,messaging_postbacks,message_reactions",
        "access_token": page_access_token
    }
    _, data = _request_json("POST", url, params=params)
    return data


class FacebookWebhook(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            if request.GET.get("hub.verify_token") == settings.FB_VERIFY_TOKEN:
                return Response(int(request.GET.get("hub.challenge")))
        except Exception as exc:
            logger.warning("Webhook verification error: %s", exc)
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
                    elif field == "messages":
                        dispatch_whatsapp_messages(entry, change)

                for event in entry.get("messaging", []):
                    dispatch_messaging(page_id, event)

        except Exception as exc:
            logger.exception("Facebook webhook processing error: %s", exc)
            return Response("EVENT_RECEIVED", status=status.HTTP_200_OK)

        return Response("EVENT_RECEIVED", status=status.HTTP_200_OK)


class InstagramWebhook(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            if request.GET.get("hub.verify_token") == settings.FB_VERIFY_TOKEN:
                return Response(int(request.GET.get("hub.challenge")))
        except Exception as exc:
            logger.warning("Instagram webhook verification error: %s", exc)
        return Response("Invalid token", status=403)

    def post(self, request):
        data = request.data
        for entry in data.get("entry", []):
            page_id = entry.get("id")
            for event in entry.get("messaging", []):
                dispatch_messaging(page_id, event)
        return Response("EVENT_RECEIVED")


class TikTokWebhook(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        expected_token = getattr(settings, "TIKTOK_VERIFY_TOKEN", settings.FB_VERIFY_TOKEN)
        verify_token = (
            request.GET.get("verify_token")
            or request.GET.get("hub.verify_token")
            or request.GET.get("token")
        )
        challenge = request.GET.get("challenge") or request.GET.get("hub.challenge")

        if verify_token and expected_token and verify_token != expected_token:
            return Response("Invalid token", status=403)
        if challenge is not None:
            return Response(challenge)
        return Response("OK", status=status.HTTP_200_OK)

    def post(self, request):
        try:
            dispatch_tiktok_feed(request.data)
        except Exception as exc:
            logger.exception("TikTok webhook processing error: %s", exc)
        return Response("EVENT_RECEIVED", status=status.HTTP_200_OK)


class MessangerConnectWithBot(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        platform = (request.data.get("platform") or "facebook").lower()

        if platform == "whatsapp":
            wa_identifier = (
                request.data.get("whatsapp_account_id")
                or request.data.get("wa_account_id")
                or request.data.get("waba_id")
                or request.data.get("phone_number_id")
                or request.data.get("page_id")
            )
            if not wa_identifier:
                return self.error(
                    message="whatsapp_account_id, waba_id or phone_number_id is required",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            wa_accounts = WhatsAppBusinessAccount.objects.filter(user=request.user)
            wa_account = None
            wa_identifier_str = str(wa_identifier).strip()
            if wa_identifier_str.isdigit():
                wa_account = wa_accounts.filter(id=int(wa_identifier_str)).first()
            if not wa_account:
                wa_account = (
                    wa_accounts.filter(phone_number_id=wa_identifier_str).first()
                    or wa_accounts.filter(waba_id=wa_identifier_str).first()
                )

            if not wa_account:
                return self.error(
                    message="WhatsApp account not found",
                    status_code=status.HTTP_404_NOT_FOUND,
                )

            social = SocialAccount.objects.filter(
                user=request.user,
                platform="whatsapp",
            ).first()
            access_token = (
                (social.long_lived_token if social else None)
                or (social.user_access_token if social else None)
                or getattr(settings, "WHATSAPP_SYSTEM_TOKEN", "")
            )
            response = _subscribe_whatsapp_waba(wa_account.waba_id, access_token)
            if response.get("error"):
                return self.error(
                    message="Failed to subscribe WhatsApp account to webhook events",
                    errors=response.get("error"),
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            return self.success(
                message="Successfully connected WhatsApp with bot",
                status_code=status.HTTP_200_OK,
                data={
                    "subscription": response,
                    "whatsapp_account": {
                        "id": wa_account.id,
                        "waba_id": wa_account.waba_id,
                        "phone_number_id": wa_account.phone_number_id,
                    },
                },
                meta={"action": "whatsapp_connect_with_bot"},
            )

        p_id = request.data.get("page_id")
        if not p_id:
            return self.error(
                message="page_id is required",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        page = None
        if platform == "instagram":
            page = InstagramAccount.objects.filter(user=request.user, id=p_id, is_active=True).first()
        else:
            page = FacebookPage.objects.filter(user=request.user, id=p_id, is_active=True).first()

        if not page:
            return self.error(
                message="Page not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        response = subscribe_page_to_messages(page.page_id, page.page_access_token)
        if response.get("error"):
            return self.error(
                message="Failed to subscribe page to webhook events",
                errors=response.get("error"),
                status_code=status.HTTP_400_BAD_REQUEST
            )

        return self.success(
            message="Successfully connected with bot",
            status_code=status.HTTP_200_OK,
            data={"subscription": response},
            meta={"action": "messanger_connect_with_bot"}
        )


class TikTokConnectURL(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        config = settings.PLATFORM_CONFIG.get("tiktok", {})
        if not config:
            return self.error(
                message="TikTok config missing",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        state = str(uuid.uuid4())
        cache.set("tiktok_oauth_" + state, request.user.id, timeout=300)

        params = {
            "client_key": config.get("client_id"),
            "response_type": "code",
            "scope": ",".join(config.get("scope", [])),
            "redirect_uri": config.get("redirect_uri"),
            "state": state,
        }
        url = f"{config.get('auth_url')}?{urlencode(params, quote_via=quote_plus)}"

        return self.success(
            message="TikTok connect URL generated successfully",
            status_code=status.HTTP_200_OK,
            data={"url": url},
            meta={"action": "tiktok_connect_url"}
        )


class FacebookDeletion(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def _disconnect_page(self, request):
        page_id = (
            request.data.get("page_id")
            or request.query_params.get("page_id")
        )
        if not page_id:
            return self.error(
                message="page_id is required",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        page = FacebookPage.objects.filter(
            id=page_id,
            user=request.user,
            is_active=True
        ).first()
        if not page:
            return self.error(
                message="Facebook page not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        _, graph_response = _request_json(
            "DELETE",
            f"{GRAPH_API_BASE}/{page.page_id}/subscribed_apps",
            params={"access_token": page.page_access_token},
        )
        page.is_active = False
        page.save(update_fields=["is_active"])
        InstagramAccount.objects.filter(
            user=request.user,
            page_id=page.page_id
        ).update(is_active=False)

        return self.success(
            message="Facebook page disconnected successfully",
            data={"graph_response": graph_response},
            status_code=status.HTTP_200_OK,
            meta={"action": "facebook_page_deleted"}
        )

    def delete(self, request):
        return self._disconnect_page(request)

    def post(self, request):
        return self._disconnect_page(request)

    def get(self, request):
        return self._disconnect_page(request)
