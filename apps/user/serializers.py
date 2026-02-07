from rest_framework import serializers
from .models import User, Account,Shop, Business,Banking
from django.contrib.auth import authenticate
from django.db import transaction
from apps.transaction.models import Transaction
from apps.subscription.models import UserSubscription
from apps.account.models import DebitCredit
from apps.courier.models import CourierOrder
from apps.voice.models import Agent
from apps.phone_number.models import PhoneNumber


class UserProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    last_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    username = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Account
        fields = [
            'id',
            'full_name',
            'phone',
            'organization',
            'first_name',
            'last_name',
            'username',
        ]
        read_only_fields = ['id']
        extra_kwargs = {
            'full_name': {'required': False, 'allow_blank': True},
            'phone': {'required': False, 'allow_null': True, 'allow_blank': True},
            'organization': {'required': False, 'allow_null': True, 'allow_blank': True},
        }

    def validate(self, attrs):
        full_name = (attrs.get('full_name') or '').strip()
        first_name = (attrs.get('first_name') or '').strip()
        last_name = (attrs.get('last_name') or '').strip()

        if not full_name:
            derived_full_name = ' '.join(part for part in [first_name, last_name] if part).strip()
            if derived_full_name:
                attrs['full_name'] = derived_full_name

        return attrs

    def update(self, instance, validated_data):
        first_name = (validated_data.pop('first_name', '') or '').strip()
        last_name = (validated_data.pop('last_name', '') or '').strip()
        username = validated_data.pop('username', None)

        full_name = (validated_data.get('full_name') or '').strip()
        if not full_name:
            derived_full_name = ' '.join(part for part in [first_name, last_name] if part).strip()
            if derived_full_name:
                validated_data['full_name'] = derived_full_name

        if username is not None:
            username = username.strip()
            validated_data['user_str_id'] = username or None

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
    

    
class UserSerializer(serializers.ModelSerializer):
    account = UserProfileSerializer(required=False)

    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'account']
        extra_kwargs = {'password': {'write_only': True}}

    def _normalize_account_data(self, account_data):
        if not account_data:
            return None

        normalized_data = dict(account_data)

        first_name = (normalized_data.pop('first_name', '') or '').strip()
        last_name = (normalized_data.pop('last_name', '') or '').strip()
        username = normalized_data.pop('username', None)

        full_name = (normalized_data.get('full_name') or '').strip()
        if not full_name:
            full_name = ' '.join(part for part in [first_name, last_name] if part).strip()
        normalized_data['full_name'] = full_name

        if username is not None:
            username = username.strip()
            normalized_data['user_str_id'] = username or None

        return normalized_data

    def create(self, validated_data):
        account_data = self._normalize_account_data(validated_data.pop('account', None))

        # Create user
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password']
        )

        # Create account if data is provided
        if account_data:
            Account.objects.create(
                user=user,
                full_name=account_data.get('full_name', ''),
                phone=account_data.get('phone', ''),
                organization=account_data.get('organization', ''),
                user_str_id=account_data.get('user_str_id')
            )

        return user

    def update(self, instance, validated_data):
        account_data = self._normalize_account_data(validated_data.pop('account', None))

        if 'password' in validated_data:
            instance.set_password(validated_data['password'])

        instance.save()

        if account_data:
            profile, _ = Account.objects.get_or_create(user=instance)
            serializer = UserProfileSerializer(profile, data=account_data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

        return instance

    
class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])  
        
        if user and user.is_active:
            return user
        raise serializers.ValidationError('Invalid credentials')
    

class AccountSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    subscription = serializers.SerializerMethodField()
    
    class Meta:
        model = Account
        fields = [
            "user_id",
            "full_name",
            "email",
            "phone",
            "balance",
            "organization",
            "last_login",
            "is_verified",
            "date_joined",
            "image",
            "role",
            "preferences",
            "subscription"
        ]
    
    # Get email from the related user
    email = serializers.EmailField(source='user.email', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)

    # Extract roles from related user
    def get_role(self, obj):
        return obj.user.role if obj.user.role else "user"
    
    

    # Placeholder subscription info
    def get_subscription(self, obj):
        # Customize if you have a subscription model
        return {
            "plan": "Free",
            "expires_at": None,
            "auto_renew": False
        }
    
    def update(self, instance, validated_data):
        instance.full_name = validated_data.get("full_name", instance.full_name)
        instance.phone = validated_data.get("phone", instance.phone)
        instance.organization = validated_data.get("organization", instance.organization)
        instance.save()
        return instance
    


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    full_name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=20)
    balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    organization = serializers.CharField(max_length=255)

    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "role",
            "full_name",
            "phone",
            "balance",
            "organization",
        ]

    def validate_role(self, value):
        parent = self.context["request"].user

        if parent.role == "reseller" and value not in ["sub_reseller", "user"]:
            raise serializers.ValidationError(
                "Reseller can create only sub reseller or user"
            )

        if parent.role == "sub_reseller":
            raise serializers.ValidationError(
                "Sub reseller cannot create users"
            )

        return value

    def create(self, validated_data):
        parent = self.context["request"].user
        password = validated_data.pop("password")

        account_data = {
            "full_name": validated_data.pop("full_name"),
            "phone": validated_data.pop("phone"),
            "organization": validated_data.pop("organization"),
        }
        with transaction.atomic():
            user = User(
                email=validated_data["email"],
                role=validated_data["role"],
                parent=parent
            )
            user.set_password(password)
            user.save()

            Account.objects.create(
                user=user,
                **account_data
            )

            return user



class ChildUserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="account.full_name", allow_null=True)
    phone = serializers.CharField(source="account.phone", allow_null=True)
    balance = serializers.DecimalField(
        source="account.balance",
        max_digits=12,
        decimal_places=2,
        allow_null=True
    )
    organization = serializers.CharField(
        source="account.organization",
        allow_null=True
    )

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "role",
            "full_name",
            "phone",
            "balance",
            "organization",
        )


    def get_name(self, obj):
        if hasattr(obj, "account"):
            return obj.account.full_name    
        return ""

    def get_phone(self, obj):
        return obj.account.phone if hasattr(obj, "account") else None

    def get_balance(self, obj):
        return obj.account.balance if hasattr(obj, "account") else 0

    def get_organization(self, obj):
        return obj.account.organization if hasattr(obj, "account") else None



# Setting > Profile > Shop Info serializers

class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = (
            "id",
            "shop_name",
            "shop_description",
            "business_email",
            "business_phone",
            "business_address",
            "website_url",
        )

# Setting > Profile > business Info serializers
class BusinessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = (
            "id",
            "business_type",
            "years_in_business",
            "business_registration_number",
            "tax_id_ein",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

# Setting > Profile > Banking Info serializers

class BankingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banking
        fields = (
            "id",
            "bank_name",
            "account_name",
            "account_number",
            "routing_number",
            "swift_bic_code",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class ResellerCustomerPaymentHistorySerializer(serializers.ModelSerializer):
    customer_id = serializers.IntegerField(source="user_id", read_only=True)
    customer_email = serializers.EmailField(source="user.email", read_only=True)
    customer_name = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = (
            "id",
            "transaction_id",
            "customer_id",
            "customer_email",
            "customer_name",
            "status",
            "category",
            "amount",
            "description",
            "purpose",
            "payment_method",
            "created_at",
        )

    def get_customer_name(self, obj):
        account = getattr(obj.user, "account", None)
        if account:
            return account.full_name
        return ""


class ResellerCustomerSubscriptionSerializer(serializers.ModelSerializer):
    customer_id = serializers.IntegerField(source="user_id", read_only=True)
    customer_email = serializers.EmailField(source="user.email", read_only=True)
    customer_name = serializers.SerializerMethodField()
    plan_name = serializers.CharField(source="plan.name", read_only=True)
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = UserSubscription
        fields = (
            "id",
            "customer_id",
            "customer_email",
            "customer_name",
            "status",
            "plan_name",
            "started_at",
            "expires_at",
            "last_renewed_at",
            "is_expired",
        )

    def get_customer_name(self, obj):
        account = getattr(obj.user, "account", None)
        if account:
            return account.full_name
        return ""

    def get_is_expired(self, obj):
        return not obj.is_active()


class ResellerCustomerDueSerializer(serializers.ModelSerializer):
    customer_id = serializers.IntegerField(source="owner_id", read_only=True)
    customer_email = serializers.EmailField(source="owner.email", read_only=True)
    customer_full_name = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()

    class Meta:
        model = DebitCredit
        fields = (
            "id",
            "customer_id",
            "customer_email",
            "customer_full_name",
            "customer_name",
            "voucher_no",
            "invoice_no",
            "payment_type",
            "entry_type",
            "amount",
            "balance",
            "due_date",
            "is_overdue",
            "created_at",
        )

    def get_customer_full_name(self, obj):
        account = getattr(obj.owner, "account", None)
        if account:
            return account.full_name
        return ""

    def get_is_overdue(self, obj):
        from django.utils import timezone

        if not obj.due_date:
            return False
        return obj.due_date < timezone.localdate()


class ResellerCustomerCourierCollectionSerializer(serializers.ModelSerializer):
    customer_id = serializers.IntegerField(source="order.user_id", read_only=True)
    customer_email = serializers.EmailField(source="order.user.email", read_only=True)
    customer_name = serializers.SerializerMethodField()
    order_id = serializers.CharField(source="order.order_id", read_only=True)
    order_customer = serializers.CharField(source="order.customer", read_only=True)
    courier_name = serializers.CharField(source="courier.name", read_only=True)

    class Meta:
        model = CourierOrder
        fields = (
            "id",
            "couriers_id",
            "tracking_id",
            "invoice",
            "status",
            "customer_id",
            "customer_email",
            "customer_name",
            "order_id",
            "order_customer",
            "courier_name",
            "recipient_name",
            "recipient_phone",
            "recipient_address",
            "delivery_fee",
            "created_at",
        )

    def get_customer_name(self, obj):
        owner = getattr(obj.order, "user", None)
        if not owner:
            return ""
        account = getattr(owner, "account", None)
        if account:
            return account.full_name
        return ""


class ResellerCustomerAgentSerializer(serializers.ModelSerializer):
    customer_id = serializers.IntegerField(source="owner_id", read_only=True)
    customer_email = serializers.EmailField(source="owner.email", read_only=True)
    customer_name = serializers.SerializerMethodField()

    class Meta:
        model = Agent
        fields = (
            "id",
            "customer_id",
            "customer_email",
            "customer_name",
            "name",
            "voice",
            "language",
            "enabled",
            "public_id",
            "created_at",
            "updated_at",
        )

    def get_customer_name(self, obj):
        account = getattr(obj.owner, "account", None)
        if account:
            return account.full_name
        return ""


class ResellerCustomerActiveNumberSerializer(serializers.ModelSerializer):
    customer_id = serializers.IntegerField(source="user_id", read_only=True)
    customer_email = serializers.EmailField(source="user.email", read_only=True)
    customer_name = serializers.SerializerMethodField()

    class Meta:
        model = PhoneNumber
        fields = (
            "id",
            "customer_id",
            "customer_email",
            "customer_name",
            "phone_number",
            "friendly_name",
            "verified",
            "number_sid",
            "price",
            "created_at",
            "updated_at",
        )

    def get_customer_name(self, obj):
        account = getattr(obj.user, "account", None)
        if account:
            return account.full_name
        return ""
