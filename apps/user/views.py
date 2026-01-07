from rest_framework import permissions, status
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.contrib.auth import get_user_model
from .serializers import UserSerializer, UserLoginSerializer, AccountSerializer, ChildUserSerializer,ShopSerializer,BusinessSerializer
from utils.base_view import BaseAPIView as APIView
from utils.permission import IsAdmin, RolePermission, IsOwnerOrParentHierarchy
from rest_framework.permissions import IsAuthenticated
from middleware.cryptography import encrypt_token
from . models import Account,Shop,Business
User = get_user_model()


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
                max_age=60 * 5
            )

            response.set_cookie(
                key="rT7u1Vb8",
                value=encrypt_token(str(refresh)),
                httponly=True,
                secure=True if request.is_secure() else False,   
                samesite="None",
                max_age=60 * 60 * 24 * 5
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
        )

        response.set_cookie(
            key="rT7u1Vb8",
            value=encrypt_token(refresh_token),
            httponly=True,
            secure=True,
            samesite="None",
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



# Setting > Profile > Shop Info APIView

class ViewShopAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            shop = Shop.objects.get(pk=pk)
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

    def patch(self, request, pk):
        try:
            shop = Shop.objects.get(pk=pk)
            serializer = ShopSerializer(
                shop,
                data=request.data,
                partial=True
            )

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

        except Shop.DoesNotExist:
            return self.error(
                message="Shop not found",
                status_code=status.HTTP_404_NOT_FOUND
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
