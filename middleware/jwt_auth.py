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
        '/media/social_posts/media/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # Skip JWT check for whitelisted paths
        if any(request.path.startswith(path) for path in self.WHITELIST):
            return self.get_response(request)
        
        resolver_match = resolve(request.path)
        view_class = resolver_match.func.view_class if hasattr(resolver_match.func, "view_class") else None

        # Skip JWT check for AllowAny views
        if view_class:
            permissions = getattr(view_class, "permission_classes", [])
            if any(p is AllowAny for p in permissions):
                return self.get_response(request)

        access_token = request.COOKIES.get("xJq93kL1")

        if access_token:
            try:
                AccessToken(access_token)
                return self.get_response(request)
            except TokenError:
                refresh_token = request.COOKIES.get("rT7u1Vb8")
                if not refresh_token:
                    return self._unauthorized("Authentication required")
                try:
                    refresh = RefreshToken(refresh_token)
                    new_access = str(refresh.access_token)
                    response = self.get_response(request)
                    response.set_cookie(
                        key="xJq93kL1",
                        value=new_access,
                        httponly=True,
                        secure=True if request.is_secure() else False,
                        samesite="Lax",
                        max_age=60 * 60 * 24
                    )
                    return response
                except TokenError:
                    return self._unauthorized("Session expired. Please login again")
        else:
            refresh_token = request.COOKIES.get("rT7u1Vb8")
            if not refresh_token:
                return self._unauthorized("Authentication required")
            try:
                refresh = RefreshToken(refresh_token)
                new_access = str(refresh.access_token)
                response = self.get_response(request)
                response.set_cookie(
                    key="xJq93kL1",
                    value=new_access,
                    httponly=True,
                    secure=True if request.is_secure() else False,
                    samesite="Lax",
                    max_age=60 * 60 * 24
                )
                return response
            except TokenError:
                return self._unauthorized("Session expired. Please login again")



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