from django.http import JsonResponse
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.permissions import AllowAny
from django.urls import resolve
from django.http import JsonResponse
from datetime import datetime
import uuid


class JWTAuthMiddleware:
    
    WHITELIST = [
        "/api/auth/login/",
        "/api/auth/register/",
        "/admin/",
        '/connect-facebook/',
        '/api/social/facebook/connect/',
        '/api/social/facebook/callback/',
        '/api/social/facebook/pages/',
        '/post-generate/',
        '/media/',
        '/admin/login/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip JWT check for whitelisted paths
        if any(request.path.startswith(path) for path in self.WHITELIST):
            response = self.get_response(request)
            return response or self._unauthorized("Authentication required")
        
        resolver_match = resolve(request.path)
        view_class = getattr(resolver_match.func, "view_class", None)

        if view_class:
            permissions = getattr(view_class, "permission_classes", [])
            if any(p is AllowAny for p in permissions):
                response = self.get_response(request)
                return response or self._unauthorized("Authentication required")

        access_token = request.COOKIES.get("xJq93kL1")
        refresh_token = request.COOKIES.get("rT7u1Vb8")

        try:
            if access_token:
                AccessToken(access_token)
            elif refresh_token:
                refresh = RefreshToken(refresh_token)
                access_token = str(refresh.access_token)
                # Set cookie later after getting response
            else:
                return self._unauthorized("Authentication required")
        except TokenError:
            try:
                refresh = RefreshToken(refresh_token)
                access_token = str(refresh.access_token)
            except TokenError:
                return self._unauthorized("Session expired. Please login again")

        # Call the view
        response = self.get_response(request) or self._unauthorized("Authentication required")

        # If we created a new access token, set cookie
        if access_token:
            response.set_cookie(
                key="xJq93kL1",
                value=access_token,
                httponly=True,
                secure=request.is_secure(),
                samesite="Lax",
                max_age=60*60*24
            )

        return response


    def _forbidden(self, message, user=None):
        response_data = {
        "status": "error",
        "status_code": 403,
        "message": message,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "request_id": str(uuid.uuid4()),
        "data": {
            "user": user 
        } if user else {},
        "meta": {
            "action": "forbidden"
        }
    }
        return JsonResponse(response_data, status=403)
    
    def _unauthorized(self, message, user=None):
        response_data = {
            "status": "error",
            "status_code": 401,
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": str(uuid.uuid4()),
            "data": {
                "user": user
            } if user else {},
            "meta": {
                "action": "unauthorized"
            }
        }
        return JsonResponse(response_data, status=401)