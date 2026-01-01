from rest_framework import serializers
from .models import Vendor


class VendorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Vendor
        fields = [
            'id',
            'shop_name',
            'shop_description',
            'business_email',
            'business_phone',
            'business_address',
            'business_registration_number',
            'tax_id',
            'business_type',
            'years_in_business',
            'website_url',
            'bank_name',
            'account_holder_name',
            'account_number',
            'routing_number',
            'swift_bic_code',
            'is_active',
            'created_at',
        ]
        read_only_fields = ['id', 'is_active', 'created_at']

    def validate_business_phone(self, value):
        if not value.isdigit():
            raise serializers.ValidationError(
                "Business phone must contain only digits"
            )
        return value

    def validate_years_in_business(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Years in business cannot be negative"
            )
        return value
