from rest_framework import authentication, exceptions
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from middleware.cryptography import decrypt_token

User = get_user_model()

class CookieJWTAuthentication(authentication.BaseAuthentication):
    """
    Authenticate users using JWT stored in cookies.
    """

    def authenticate(self, request):
        token = decrypt_token(request.COOKIES.get("xJq93kL1"))
        if request.path.startswith("/api/auth/login/"):
            return None
        if not token:
            refresh_token = decrypt_token(request.COOKIES.get("rT7u1Vb8"))
            if not refresh_token:
                return None
            try:
                refresh = RefreshToken(refresh_token)
                token = str(refresh.access_token)
            except TokenError:
                return None

        try:
            payload = AccessToken(token)
            user_id = payload["user_id"]
            user = User.objects.get(id=user_id)
            return (user, token)
        except Exception as e:
            refresh_token = decrypt_token(request.COOKIES.get("rT7u1Vb8"))
            if not refresh_token:
                return None
            try:
                refresh = RefreshToken(refresh_token)
                payload = AccessToken(str(refresh.access_token))
                user_id = payload["user_id"]
                user = User.objects.get(id=user_id)
                return (user, token)
            except TokenError:
                raise exceptions.AuthenticationFailed("Invalid or expired token")
