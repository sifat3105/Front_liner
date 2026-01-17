from rest_framework import serializers
from .models import User, Account,Shop, Business,Banking
from django.contrib.auth import authenticate


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'full_name', 'phone',  'organization']
        read_only_fields = ['id']

    def update(self, instance, validated_data):
        # Update profile fields dynamically
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

    def create(self, validated_data):
        account_data = validated_data.pop('account', None)

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
                organization=account_data.get('organization', '')
            )

        return user

    def update(self, instance, validated_data):
        account_data = validated_data.pop('account', None)

        if 'password' in validated_data:
            instance.set_password(validated_data['password'])

        instance.save()

        if account_data:
            profile = instance.account
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
    roles = serializers.SerializerMethodField()
    subscription = serializers.SerializerMethodField()
    
    class Meta:
        model = Account
        fields = [
            "user_id",
            "name",
            "email",
            "phone",
            "balance",
            "organization",
            "last_login",
            "is_verified",
            "date_joined",
            "image",
            "roles",
            "preferences",
            "subscription"
        ]
    
    # Get email from the related user
    email = serializers.EmailField(source='user.email', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)

    # Extract roles from related user
    def get_roles(self, obj):
        return [obj.user.role] if obj.user.role else ["user"]
    
    

    # Placeholder subscription info
    def get_subscription(self, obj):
        # Customize if you have a subscription model
        return {
            "plan": "Free",
            "expires_at": None,
            "auto_renew": False
        }
    
    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.phone = validated_data.get("phone", instance.phone)
        instance.organization = validated_data.get("organization", instance.organization)
        instance.save()
        return instance
    


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=20)
    balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    organization = serializers.CharField(max_length=255)

    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "role",
            "name",
            "phone",
            "balance",
            "organization",
        ]

    def validate_role(self, value):
        parent = self.context["request"].user

        if parent.role == "reseller" and value != "sub_reseller":
            raise serializers.ValidationError(
                "Reseller can create only sub reseller"
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
            "name": validated_data.pop("name"),
            "phone": validated_data.pop("phone"),
            "balance": validated_data.pop("balance"),
            "organization": validated_data.pop("organization"),
        }

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
    name = serializers.CharField(source="account.name", allow_null=True)
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
            "name",
            "phone",
            "balance",
            "organization",
        )


    def get_name(self, obj):
        if hasattr(obj, "account"):
            return obj.account.name
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
