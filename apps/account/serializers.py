from rest_framework import serializers
import re
from .models import (
    Income, Refund,
    DebitCredit,
    ProfitLossReport, Sells,
    Payment
)


class IncomeSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Income
        fields = '__all__'
        read_only_fields = ('id','customer', 'created_at', 'updated_at')


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

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id', 'voucher_no', 'receiver_name', 'product',
            'quantity', 'amount', 'payment_method', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
