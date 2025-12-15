from rest_framework import permissions, status
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.contrib.auth import get_user_model
from .serializers import UserSerializer, UserLoginSerializer, AccountSerializer, ChildUserSerializer
from utils.base_view import BaseAPIView as APIView
from utils.permission import IsAdmin, RolePermission, IsOwnerOrParentHierarchy
from . models import Account
User = get_user_model()


class UserRegistrationView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "register"
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            user = serializer.instance
            refresh = RefreshToken.for_user(user)
            return self.success(
                message="User created successfully",
                status_code=status.HTTP_201_CREATED,
                data={
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "user": serializer.data
                },
                meta={"action": "registration"}
            )

        return self.error(
            message="Invalid data",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST,
            meta={"action": "registration"}
        )

class UserLoginView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"
    permission_classes = []

    def post(self, request):
        try:
            serializer = UserLoginSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                user = serializer.validated_data
                refresh = RefreshToken.for_user(user)
                return self.success(
                        message="User created successfully",
                        status_code=status.HTTP_200_OK,
                        data={
                            "refresh": str(refresh),
                            "access": str(refresh.access_token),
                            "user": serializer.data
                        },
                        meta={"action": "login"}
                    )

            return self.error(
                message="Invalid data",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
                meta={"action": "login"}
            )
        except Exception as e:
            return self.error(
                message="Invalid data",
                errors={"detail": str(e)},
                status_code=status.HTTP_400_BAD_REQUEST,
                meta={"action": "login"}
            )
        
class RefreshTokenRotationView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "refresh"
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        refresh_token_str = request.data.get("refresh")

        if not refresh_token_str:
            return self.error(
                message="Refresh token is required",
                status_code=status.HTTP_400_BAD_REQUEST,
                meta={"action": "refresh"}
            )

        try:
            refresh_token = RefreshToken(refresh_token_str)
            # Rotate if enabled in settings
            new_access = str(refresh_token.access_token)
            new_refresh = None

            # Only rotate if ROTATE_REFRESH_TOKENS = True
            from django.conf import settings
            if getattr(settings, "SIMPLE_JWT", {}).get("ROTATE_REFRESH_TOKENS", False):
                refresh_token.blacklist()  # blacklist old token
                new_refresh_obj = RefreshToken.for_user(refresh_token.payload["user_id"])
                new_refresh = str(new_refresh_obj)
                new_access = str(new_refresh_obj.access_token)

            return self.success(
                message="Refresh token rotated successfully",
                status_code=status.HTTP_200_OK,
                data={
                    "access": new_access,
                    "refresh": new_refresh or str(refresh_token)
                },
                meta={"action": "refresh"}
            )
        except TokenError as e:
            return self.error(
                message="Invalid token",
                errors={"detail": str(e)},
                status_code=status.HTTP_400_BAD_REQUEST,
                meta={"action": "refresh"}
            )
        

class LogoutView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "logout"
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        refresh_token_str = request.data.get("refresh")
        if not refresh_token_str:
            return self.error(
                message="Refresh token is required",
                status_code=status.HTTP_400_BAD_REQUEST,
                meta={"action": "logout"}
            )
        try:
            refresh_token = RefreshToken(refresh_token_str)
            refresh_token.blacklist()  # blacklist old token
            return self.success(
                message="Logout successful",
                status_code=status.HTTP_200_OK,
                meta={"action": "logout"}
            )
        except TokenError as e:
            return self.error(
                message="Invalid token",
                errors={"detail": str(e)},
                status_code=status.HTTP_400_BAD_REQUEST,
                meta={"action": "logout"}
            )
        

class AccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        account = Account.objects.get_or_create(user=request.user)[0]
        # account = request.user.account
        serializer = AccountSerializer(account)
        return self.success(
            message="Account fetched successfully",
            status_code=status.HTTP_200_OK,
            data=serializer.data
        )
    
    def put(self, request):
        account = request.user.account
        serializer = AccountSerializer(account, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return self.success(
                message="Account updated successfully",
                status_code=status.HTTP_200_OK,
                data=serializer.data
            )
        return self.error(
            message="Invalid data",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    


class CreateChildUserView(APIView):
    allowed_roles = ["seller", "sub_seller"]
    permission_classes = [RolePermission]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return self.success(
                message="User created successfully",
                status_code=status.HTTP_201_CREATED,
                data=serializer.data
            )
        return self.error(
            message="Invalid data",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
class ViewChildUserListView(APIView):
    allowed_roles = ["seller", "sub_seller"]
    permission_classes = [RolePermission]

    def get(self, request):
        users = User.objects.filter(parent=request.user)
        serializer = ChildUserSerializer(users, many=True)
        return self.success(
            message="User fetched successfully",
            status_code=status.HTTP_200_OK,
            data=serializer.data
        )

class ViewChildUserView(APIView):
    allowed_roles = ["seller", "sub_seller"]
    permission_classes = [RolePermission]

    def get(self, request, pk):
        user = User.objects.get(pk=pk)
        serializer = ChildUserSerializer(user)
        return self.success(
            message="User fetched successfully",
            status_code=status.HTTP_200_OK,
            data=serializer.data
        )

class UpdateChildUserView(APIView):
    allowed_roles = ["seller", "sub_seller"]
    permission_classes = [RolePermission]

    def put(self, request, pk):
        user = User.objects.get(pk=pk)
        serializer = ChildUserSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return self.success(
                message="User updated successfully",
                status_code=status.HTTP_200_OK,
                data=serializer.data
            )
        return self.error(
            message="Invalid data",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


    


    

