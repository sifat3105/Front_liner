from rest_framework import permissions, status
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from utils.base_view import BaseAPIView as APIView
from utils.permission import IsAdmin, RolePermission, IsOwnerOrParentHierarchy
from rest_framework.permissions import IsAuthenticated
from middleware.cryptography import encrypt_token
from django.contrib.auth import get_user_model
from django.template.context_processors import request
from datetime import datetime, timedelta
User = get_user_model()
from . models import Account,Shop,Business,Banking
from .serializers import (
    UserSerializer,
    UserLoginSerializer,
    AccountSerializer, 
    ChildUserSerializer,
    ShopSerializer,
    BusinessSerializer,
    BankingSerializer
)


class UserRegistrationView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "register"
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        email = request.data.get('email')
        if User.objects.filter(email=email).exists():
            return self.error(
                message= "User with this email already exists.",
                errors={"email": ["This email is already taken."]},
                status_code=status.HTTP_400_BAD_REQUEST,
                meta={"action": "registration"}
            )
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            user = serializer.instance
            refresh = RefreshToken.for_user(user)
            response = self.success(
                message="User created successfully",
                status_code=status.HTTP_201_CREATED,
                data={
                    "user": serializer.data
                },
                meta={"action": "registration"}
            )
            response.set_cookie(
                key="xJq93kL1",
                value=encrypt_token(str(refresh.access_token)),
                httponly=True,
                secure=True if request.is_secure() else False,
                samesite="None",
                expires=datetime.utcnow() + timedelta(weeks=99999)
            )

            response.set_cookie(
                key="rT7u1Vb8",
                value=encrypt_token(str(refresh)),
                httponly=True,
                secure=True if request.is_secure() else False,   
                samesite="None",
                expires=datetime.utcnow() + timedelta(weeks=99999)
            )

            return response

        return self.error(
            message="Invalid data",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST,
            meta={"action": "registration"}
        )

class UserLoginView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")


        if not email or not password:
            return self.error(
                message="Email and password required",
                status_code=status.HTTP_400_BAD_REQUEST,
                meta={"action": "login"}
            )

        try:
            user = User.objects.only("id", "email", "password", "is_active").get(email=email)
        except User.DoesNotExist:
            return self.error(
                message="Invalid credentials",
                status_code=status.HTTP_400_BAD_REQUEST,
                meta={"action": "login"}
            )

        if not user.is_active or not user.check_password(password):
            return self.error(
                message="Invalid credentials",
                status_code=status.HTTP_400_BAD_REQUEST,
                meta={"action": "login"}
            )

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response = self.success(
            message="Login successful",
            status_code=status.HTTP_200_OK,
            data={
                "user": {
                    "id": user.id,
                    "email": user.email
                }
            },
            meta={"action": "login"}
        )

        response.set_cookie(
            key="xJq93kL1",
            value=encrypt_token(access_token),
            httponly=True,
            secure=True,
            samesite="None",
            expires=datetime.utcnow() + timedelta(weeks=99999)
        )

        response.set_cookie(
            key="rT7u1Vb8",
            value=encrypt_token(refresh_token),
            httponly=True,
            secure=True,
            samesite="None",
            expires=datetime.utcnow() + timedelta(weeks=99999)
        )

        return response

        
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
        try:
            # Get refresh token from cookie
            refresh_token = request.COOKIES.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()  # Invalidate refresh token

            # Delete cookies
            response = self.success(
                message="Logged out successfully",
                status_code=status.HTTP_200_OK,
                meta={"action": "logout"}
            )
            response.delete_cookie("xJq93kL1")
            response.delete_cookie("rT7u1Vb8")

            return response

        except Exception as e:
            return self.error(
                message="Logout failed",
                errors={"detail": str(e)},
                status_code=status.HTTP_400_BAD_REQUEST
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
    
    def patch(self, request):
        account = request.user.account
        serializer = AccountSerializer(account, data=request.data, partial=True)
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



# Setting > Profile > Shop Info APIView

class ViewShopAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            shop = Shop.objects.filter(owner=request.user).first()
            serializer = ShopSerializer(shop)
            return self.success(
                message="Shop fetched successfully",
                status_code=status.HTTP_200_OK,
                data=serializer.data
            )
        except Shop.DoesNotExist:
            return self.error(
                message="Shop not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

class UpdateShopAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Each user has only one shop
        try:
            return self.request.user.shop.first()
        except Shop.DoesNotExist:
            return None

    def patch(self, request, format=None):
        shop = self.get_object()
        if not shop:
            return self.error(
                message="Shop not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = ShopSerializer(shop, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return self.success(
                message="Shop updated successfully",
                status_code=status.HTTP_200_OK,
                data=serializer.data
            )
        return self.error(
            message="Invalid data",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


# Setting > Profile > business Info APIView

class BusinessRetrieveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        business = Business.objects.filter(owner=request.user).first()

        if not business:
            return self.error(
                message="Business not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = BusinessSerializer(business)
        return self.success(
            message="Business fetched successfully",
            status_code=status.HTTP_200_OK,
            data=serializer.data
        )

class BusinessUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        business = Business.objects.filter(owner=request.user).first()

        if not business:
            return self.error(
                message="Business not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = BusinessSerializer(
            business,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return self.success(
                message="Business updated successfully",
                status_code=status.HTTP_200_OK,
                data=serializer.data
            )

        return self.error(
            message="Invalid data",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )

# Setting > Profile > Banking Info APIView

class BankingDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        banking = Banking.objects.filter(owner=request.user).first()

        if not banking:
            return self.error(
                message="Banking information not found",
                status_code=status.HTTP_200_OK
            )

        serializer = BankingSerializer(banking)
        return self.success(
            message="Banking information fetched successfully",
            status_code=status.HTTP_200_OK,
            data=serializer.data
        )

class BankingUpdateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        banking = Banking.objects.filter(owner=request.user).first()

        if not banking:
            return self.error(
                message="Banking information not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = BankingSerializer(
            banking,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return self.success(
                message="Banking information updated successfully",
                status_code=status.HTTP_200_OK,
                data=serializer.data
            )

        return self.error(
            message="Invalid data",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class ChangePasswordAPIView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def patch (self, request):
        
        user = request.user

        current_password = request.data.get("current_password")
        new_password = request.data.get("new_password")
        confirm_new_password = request.data.get("confirm_new_password")

        # New password match check
        if new_password != confirm_new_password:
            return self.error(
                message="New password and confirm password do not match",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors={
                    "confirm_new_password": "Password mismatch"
                }
            )

        # Current password check with DB
        if not user.check_password(current_password):
            return self.error(
                message="Current password is incorrect",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors={
                    "current_password": "Invalid current password"
                }
            )

        # Save new password
        user.set_password(new_password)
        user.save()

        return self.success(
            message="Password updated successfully",
            status_code=status.HTTP_200_OK,
            meta={
                "action": "change_password"
            }
        )
