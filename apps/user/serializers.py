from rest_framework import serializers
from .models import User, Account,Shop, Business,Banking
from django.contrib.auth import authenticate


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'first_name', 'full_name', 'phone', 'username', 'organization']
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
                first_name=account_data.get('first_name', ''),
                full_name=account_data.get('full_name', ''),
                username=account_data.get('username', ''),
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
            "full_name",
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
        instance.full_name = validated_data.get("full_name", instance.full_name)
        instance.phone = validated_data.get("phone", instance.phone)
        instance.organization = validated_data.get("organization", instance.organization)
        instance.save()
        return instance
    

class ChildUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'role', 'name', 'phone', 'balance', 'organization']

    name = serializers.SerializerMethodField()
    phone = serializers.CharField(source='account.phone', read_only=True)
    balance = serializers.DecimalField(source='account.balance', read_only=True, decimal_places=2, max_digits=12)
    balance = serializers.DecimalField(source='account.balance', max_digits=10,decimal_places=2,read_only=True)
    organization = serializers.CharField(source='account.organization', read_only=True)

    def get_name(self, obj):
        return f"{obj.account.first_name} {obj.account.full_name}"
    

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
