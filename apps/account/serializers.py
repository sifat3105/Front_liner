from rest_framework import serializers
import re
from .models import (
    Income, Payments,
    CustomerRefund,
    VoucherType, 
    VoucherEntry,
    ProfitLossReport,
    Receiver, Product, 
    Invoice, Payment,
)


class IncomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Income
        fields = '__all__'
        read_only_fields = ('owner', 'created_at', 'updated_at')


class PaymentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payments
        fields = '__all__'
        read_only_fields = ('owner', 'created_at', 'updated_at')



# Refund Orders serializers section
class CustomerRefundSerializer(serializers.ModelSerializer):

    # Optionally, display owner's username instead of ID
    owner_username = serializers.CharField(source='owner.username', read_only=True)

    class Meta:
        model = CustomerRefund
        fields = [
            'id',
            'owner',
            'owner_username',  # convenient field for frontend display
            'location',
            'contact',
            'price',
            'platform',
            'refund_status',
        ]
        read_only_fields = ['id', 'owner', 'owner_username']

    def create(self, validated_data):
        """
        Automatically assign the logged-in user as owner if not provided. 
        """
        request = self.context.get('request')
        if request and not validated_data.get('owner'):
            validated_data['owner'] = request.user
        return super().create(validated_data)
    

# Voucher Type Serializer
class VoucherTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = VoucherType

        fields = [
            'id',
            'name',
            'is_active',
        ]
        read_only_fields = ['id']


# Voucher Entry Serializer
class VoucherEntrySerializer(serializers.ModelSerializer):

    owner_username = serializers.CharField(
        source='owner.username',
        read_only=True
    )

    # Voucher type show
    voucher_type_name = serializers.CharField(
        source='voucher_type.name',
        read_only=True
    )

    class Meta:
        model = VoucherEntry

        # Explicit field list (best practice)
        fields = [
            'id',
            'voucher_no',
            'voucher_date',
            'customer_name',

            'voucher_type',
            'voucher_type_name',

            'nature',
            'debit',
            'credit',
            'total_debit',
            'total_credit',
            'amount',

            'status',
            'posted',
            'due_date',

            'owner',
            'owner_username',

            'created_at',
        ]

        # Disable API edit 
        read_only_fields = [
            'id',
            'owner',
            'owner_username',
            'total_debit',
            'total_credit',
            'created_at',
        ]

    # Custom Validation
    def validate(self, attrs):

        nature = attrs.get('nature')
        debit = attrs.get('debit', 0)
        credit = attrs.get('credit', 0)

        # Debit voucher হলে credit দেওয়া যাবে না
        if nature == 'debit' and credit > 0:
            raise serializers.ValidationError(
                "Debit voucher এ credit amount দেওয়া যাবে না।"
            )

        # Credit voucher হলে debit দেওয়া যাবে না
        if nature == 'credit' and debit > 0:
            raise serializers.ValidationError(
                "Credit voucher এ debit amount দেওয়া যাবে না।"
            )

        return attrs

    # Auto assign owner
    def create(self, validated_data):

        request = self.context.get('request')
        if request and request.user:
            validated_data['owner'] = request.user

        return super().create(validated_data)


# Profit & Loss (P&L) sectiont
class ProfitLossReportSerializer(serializers.ModelSerializer):
    """
    Serializer for Profit & Loss Report
    """

    class Meta:
        model = ProfitLossReport

        fields = [
            'id',
            'date',
            'revenue',
            'expenses',
            'gross_profit',
            'operating_expenses',
            'net_profit',
            'status',
            'created_at',
        ]

        read_only_fields = [
            'id',
            'gross_profit',
            'net_profit',
            'created_at',
        ]



# Payment section
class ReceiverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receiver
        fields = ('id', 'name', 'receiver_type')



class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('id', 'name', 'description')



class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ('id', 'invoice_number', 'receiver', 'created_at')


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            'id',
            'receiver',
            'product',
            'invoice',
            'description',
            'quantity',
            'amount',
            'payment_method',
            'cheque_number',
            'created_at',
        )
        read_only_fields = ["receiver"]
    def create(self, validated_data):
        receiver = self.context.get('receiver')
        validated_data['receiver'] = receiver
        return super().create(validated_data)

    # def validate(self, data):
    #     receiver = data.get('receiver')
    #     invoice = data.get('invoice')
    #     payment_method = data.get('payment_method')
    #     cheque_number = data.get('cheque_number')

    #     # Supplier must have invoice
    #     if receiver.receiver_type == 'supplier' and not invoice:
    #         raise serializers.ValidationError({
    #             "invoice": "Invoice is required for supplier."
    #         })

    #     # User cannot have invoice
    #     if receiver.receiver_type == 'user' and invoice:
    #         raise serializers.ValidationError({
    #             "invoice": "Invoice is not allowed for user."
    #         })

    #     # Cheque number validation
    #     if payment_method == 'cheque' and not cheque_number:
    #         raise serializers.ValidationError({
    #             "cheque_number": "Cheque number is required for cheque payment."
    #         })

    #     if payment_method != 'cheque' and cheque_number:
    #         raise serializers.ValidationError({
    #             "cheque_number": "Cheque number should be empty for non-cheque payment."
    #         })

    #     return data
