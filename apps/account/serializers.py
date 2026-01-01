from rest_framework import serializers
import re
from .models import (
    Income, Payments,
    Refund,
    DebitCredit,
    ProfitLossReport,
    Receiver, Product, 
    Invoice, Payment,
    Sells,
)


class IncomeSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Income
        fields = '__all__'
        read_only_fields = ('customer', 'created_at', 'updated_at')


class PaymentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payments
        fields = '__all__'
        read_only_fields = ('owner', 'created_at', 'updated_at')



# Sell Orders serializers section
class CustomerSellsSerializer(serializers.ModelSerializer):

    # Optionally, display owner's username instead of ID
    owner_username = serializers.CharField(source='owner.username', read_only=True)

    class Meta:
        model = Sells
        fields = [
            'id',
            'owner',
            'owner_username',  # convenient field for frontend display
            'order_id',
            'customer',
            'location',
            'contact',
            'order_amount',
            'platform',
            'sells_status',
        ]
        read_only_fields = ['id', 'owner', 'owner_username']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and not validated_data.get('owner'):
            validated_data['owner'] = request.user
        return super().create(validated_data)



# Refund Orders serializers section
class CustomerRefundSerializer(serializers.ModelSerializer):

    # Optionally, display owner's username instead of ID
    owner_username = serializers.CharField(source='owner.username', read_only=True)

    class Meta:
        model = Refund
        fields = [
            'id',
            'owner',
            'owner_username',  # convenient field for frontend display
            'order_id',
            'customer',
            'location',
            'contact',
            'order_amount',
            'platform',
            'refund_status',
        ]
        read_only_fields = ['id', 'owner', 'owner_username']

    def create(self, validated_data):

        request = self.context.get('request')
        if request and not validated_data.get('owner'):
            validated_data['owner'] = request.user
        return super().create(validated_data)
    

# Debit Credit serializers section

class DebitCreditSerializer(serializers.ModelSerializer):

    class Meta:
        model = DebitCredit
        fields = '__all__'
        read_only_fields = ('debit', 'credit', 'balance', 'created_at')

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)

# Profit & Loss (P&L) sectiont
class ProfitLossReportSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProfitLossReport

        fields = [
            'id',
            'date',
            'revenue',
            'expenses',
            'gross_profit',
            'net_profit',
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
