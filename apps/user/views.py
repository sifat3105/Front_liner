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
from django.utils import timezone
from django.utils.dateparse import parse_date
User = get_user_model()
from . models import Account,Shop,Business,Banking
from apps.transaction.models import Transaction
from apps.subscription.models import UserSubscription
from apps.account.models import DebitCredit
from apps.courier.models import CourierOrder
from apps.voice.models import Agent
from apps.phone_number.models import PhoneNumber
from .serializers import (
    UserSerializer,
    UserLoginSerializer,
    AccountSerializer, 
    ChildUserSerializer,
    ShopSerializer,
    BusinessSerializer,
    BankingSerializer,
    UserCreateSerializer,
    ResellerCustomerPaymentHistorySerializer,
    ResellerCustomerSubscriptionSerializer,
    ResellerCustomerDueSerializer,
    ResellerCustomerCourierCollectionSerializer,
    ResellerCustomerAgentSerializer,
    ResellerCustomerActiveNumberSerializer,
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
        serializer = AccountSerializer(account, context = {'request': request})
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
    
class UserCreateAPIView(APIView):
    allowed_roles = ["seller", "sub_seller", "reseller"]
    permission_classes = [RolePermission]

    def post(self, request):
        serializer = UserCreateSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return self.success(
            message="User created successfully",
            data={
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "full_name": user.account.full_name,
                "phone": user.account.phone,
                "balance": user.account.balance,
                "organization": user.account.organization,
            },
            status_code=status.HTTP_201_CREATED
        )

class CreateChildUserView(APIView):
    allowed_roles = ["seller", "sub_seller", "reseller"]
    permission_classes = [RolePermission]

    def post(self, request):
        if request.user.role not in ["seller", "sub_seller", "reseller"]:
            return self.error(
                message="Only sellers, sub-sellers and resellers can create child users",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        serializer = UserCreateSerializer(data=request.data, context={"request": request})
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
    allowed_roles = ["superuser", "admin", "seller", "sub_seller", "reseller"]
    permission_classes = [RolePermission]



    def get(self, request):
        users = (User.objects.filter(parent=request.user).select_related("account"))

        serializer = ChildUserSerializer(users, many=True)

        return self.success(
            message="User fetched successfully",
            status_code=status.HTTP_200_OK,
            data={
                "count": users.count(),
                "users": serializer.data
            }
        )
    


class ViewChildUserView(APIView):
    allowed_roles = ["seller", "sub_seller", "reseller"]
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
    allowed_roles = ["seller", "sub_seller", "reseller"]
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


class ResellerHierarchyMixin:
    def _get_descendant_user_ids(self, root_user):
        discovered_ids = set()
        frontier = [root_user.id]

        while frontier:
            child_ids = list(
                User.objects.filter(parent_id__in=frontier).values_list("id", flat=True)
            )
            next_frontier = []
            for child_id in child_ids:
                if child_id not in discovered_ids:
                    discovered_ids.add(child_id)
                    next_frontier.append(child_id)
            frontier = next_frontier

        return list(discovered_ids)


class ResellerCustomerPaymentHistoryAPIView(ResellerHierarchyMixin, APIView):
    allowed_roles = ["reseller", "sub_reseller"]
    permission_classes = [RolePermission]

    def get(self, request):
        descendant_ids = self._get_descendant_user_ids(request.user)
        if not descendant_ids:
            return self.success(
                message="Customer payment history fetched successfully",
                data={"count": 0, "payments": []},
                status_code=status.HTTP_200_OK,
                meta={"action": "reseller-customer-payment-history"},
            )

        queryset = (
            Transaction.objects.filter(user_id__in=descendant_ids)
            .select_related("user", "user__account")
            .order_by("-created_at")
        )

        customer_id = request.query_params.get("customer_id")
        if customer_id:
            queryset = queryset.filter(user_id=customer_id)

        transaction_status = request.query_params.get("status")
        if transaction_status:
            queryset = queryset.filter(status=transaction_status)

        category = request.query_params.get("category")
        if category:
            queryset = queryset.filter(category=category)

        start_date = parse_date(request.query_params.get("start_date", ""))
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)

        end_date = parse_date(request.query_params.get("end_date", ""))
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)

        serializer = ResellerCustomerPaymentHistorySerializer(queryset, many=True)
        return self.success(
            message="Customer payment history fetched successfully",
            data={"count": queryset.count(), "payments": serializer.data},
            status_code=status.HTTP_200_OK,
            meta={"action": "reseller-customer-payment-history"},
        )


class ResellerCustomerDueExpireAPIView(ResellerHierarchyMixin, APIView):
    allowed_roles = ["reseller", "sub_reseller"]
    permission_classes = [RolePermission]

    def get(self, request):
        descendant_ids = self._get_descendant_user_ids(request.user)
        if not descendant_ids:
            return self.success(
                message="Customer due and expiry data fetched successfully",
                data={
                    "summary": {
                        "total_subscriptions": 0,
                        "expired_subscriptions": 0,
                        "total_dues": 0,
                        "overdue_dues": 0,
                    },
                    "subscriptions": [],
                    "dues": [],
                },
                status_code=status.HTTP_200_OK,
                meta={"action": "reseller-customer-due-expire"},
            )

        customer_id = request.query_params.get("customer_id")
        filtered_ids = descendant_ids
        if customer_id:
            try:
                customer_id = int(customer_id)
            except (TypeError, ValueError):
                return self.error(
                    message="customer_id must be an integer",
                    status_code=status.HTTP_400_BAD_REQUEST,
                    meta={"action": "reseller-customer-due-expire"},
                )
            filtered_ids = [customer_id] if customer_id in descendant_ids else []

        subscriptions = (
            UserSubscription.objects.filter(user_id__in=filtered_ids)
            .select_related("user", "user__account", "plan")
            .order_by("expires_at")
        )
        dues = (
            DebitCredit.objects.filter(owner_id__in=filtered_ids, due_date__isnull=False)
            .select_related("owner", "owner__account")
            .order_by("due_date")
        )

        subscription_data = ResellerCustomerSubscriptionSerializer(subscriptions, many=True).data
        due_data = ResellerCustomerDueSerializer(dues, many=True).data
        expired_subscriptions = sum(1 for sub in subscriptions if not sub.is_active())
        overdue_dues = dues.filter(due_date__lt=timezone.localdate()).count()

        return self.success(
            message="Customer due and expiry data fetched successfully",
            data={
                "summary": {
                    "total_subscriptions": subscriptions.count(),
                    "expired_subscriptions": expired_subscriptions,
                    "total_dues": dues.count(),
                    "overdue_dues": overdue_dues,
                },
                "subscriptions": subscription_data,
                "dues": due_data,
            },
            status_code=status.HTTP_200_OK,
            meta={"action": "reseller-customer-due-expire"},
        )


class ResellerCustomerCollectionCourierAPIView(ResellerHierarchyMixin, APIView):
    allowed_roles = ["reseller", "sub_reseller"]
    permission_classes = [RolePermission]

    def get(self, request):
        descendant_ids = self._get_descendant_user_ids(request.user)
        if not descendant_ids:
            return self.success(
                message="Customer courier collection list fetched successfully",
                data={"count": 0, "collections": []},
                status_code=status.HTTP_200_OK,
                meta={"action": "reseller-customer-courier-collection"},
            )

        queryset = (
            CourierOrder.objects.filter(order__user_id__in=descendant_ids)
            .select_related("order", "order__user", "order__user__account", "courier")
            .order_by("-created_at")
        )

        customer_id = request.query_params.get("customer_id")
        if customer_id:
            queryset = queryset.filter(order__user_id=customer_id)

        courier_status = request.query_params.get("status", "collected")
        if courier_status and courier_status.lower() != "all":
            queryset = queryset.filter(status__iexact=courier_status)

        serializer = ResellerCustomerCourierCollectionSerializer(queryset, many=True)
        return self.success(
            message="Customer courier collection list fetched successfully",
            data={"count": queryset.count(), "collections": serializer.data},
            status_code=status.HTTP_200_OK,
            meta={"action": "reseller-customer-courier-collection"},
        )


class ResellerAgentListAPIView(ResellerHierarchyMixin, APIView):
    allowed_roles = ["reseller", "sub_reseller"]
    permission_classes = [RolePermission]

    def get(self, request):
        descendant_ids = self._get_descendant_user_ids(request.user)
        if not descendant_ids:
            return self.success(
                message="Customer agent list fetched successfully",
                data={"count": 0, "agents": []},
                status_code=status.HTTP_200_OK,
                meta={"action": "reseller-agent-list"},
            )

        queryset = (
            Agent.objects.filter(owner_id__in=descendant_ids)
            .select_related("owner", "owner__account")
            .order_by("-updated_at")
        )

        customer_id = request.query_params.get("customer_id")
        if customer_id:
            queryset = queryset.filter(owner_id=customer_id)

        enabled = request.query_params.get("enabled")
        if enabled is not None:
            enabled_value = enabled.lower()
            if enabled_value in ["true", "false"]:
                queryset = queryset.filter(enabled=(enabled_value == "true"))

        serializer = ResellerCustomerAgentSerializer(queryset, many=True)
        return self.success(
            message="Customer agent list fetched successfully",
            data={"count": queryset.count(), "agents": serializer.data},
            status_code=status.HTTP_200_OK,
            meta={"action": "reseller-agent-list"},
        )


class ResellerActiveNumberListAPIView(ResellerHierarchyMixin, APIView):
    allowed_roles = ["reseller", "sub_reseller"]
    permission_classes = [RolePermission]

    def get(self, request):
        descendant_ids = self._get_descendant_user_ids(request.user)
        if not descendant_ids:
            return self.success(
                message="Customer active number list fetched successfully",
                data={"count": 0, "numbers": []},
                status_code=status.HTTP_200_OK,
                meta={"action": "reseller-active-number-list"},
            )

        queryset = (
            PhoneNumber.objects.filter(user_id__in=descendant_ids)
            .select_related("user", "user__account")
            .order_by("-created_at")
        )

        customer_id = request.query_params.get("customer_id")
        if customer_id:
            queryset = queryset.filter(user_id=customer_id)

        active_only = request.query_params.get("active_only", "true").lower() == "true"
        if active_only:
            queryset = queryset.filter(verified=True)

        serializer = ResellerCustomerActiveNumberSerializer(queryset, many=True)
        return self.success(
            message="Customer active number list fetched successfully",
            data={"count": queryset.count(), "numbers": serializer.data},
            status_code=status.HTTP_200_OK,
            meta={"action": "reseller-active-number-list"},
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

# Setting > Profile > Change Password Info APIView

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
