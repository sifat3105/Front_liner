from rest_framework import serializers
from .models import Vendor,VendorInvoice
from django.db.models import Sum


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


# Vendor Payment History
class VendorPaymentHistorySerializer(serializers.ModelSerializer):

    vendor_name = serializers.CharField(source='vendor.shop_name', read_only=True)
    payment = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    due_payment = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = VendorInvoice
        fields = [
            'id',
            'vendor_name',
            'invoice_number',
            'invoice_date',
            'invoice_amount',
            'payment',
            'due_payment',
            'status',
        ]

    def get_status(self, obj):
        return "PAID" if obj.due_payment == 0 else "DUE"
