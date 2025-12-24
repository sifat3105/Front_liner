from rest_framework import serializers
from .models import Invoice, InvoiceItem, AdminInvoice, AdminInvoiceItem
from django.contrib.auth import get_user_model
import json

User = get_user_model()

# ------------------------------
# Invoice Serializers
# ------------------------------

class InvoiceItemSerializer(serializers.ModelSerializer):
    total = serializers.ReadOnlyField()

    class Meta:
        model = InvoiceItem
        fields = ['id', 'description', 'qty', 'unit_price', 'total']
        
class InvoiceSerializer(serializers.ModelSerializer):
    items = serializers.CharField(write_only=True)
    create_date = serializers.DateTimeField(read_only=True, source='created_at')

    class Meta:
        model = Invoice
        fields = ['customer', 'agent', 'create_date', 'due_date', 'discount', 'total_amount', 'status', 'notes', 'image', 'items']

    def create(self, validated_data):
        items_data = json.loads(validated_data.pop('items'))
        invoice = Invoice.objects.create(**validated_data)
        for item in items_data:
            InvoiceItem.objects.create(invoice=invoice, **item)
        return invoice


class InvoiceListSerializer(serializers.ModelSerializer):
    create_date = serializers.DateTimeField(read_only=True, source='created_at')
    class Meta:
        model = Invoice
        fields = ['id', 'customer', 'agent', 'create_date', 'due_date', 'total_amount', 'status']


class InvoiceDetailSerializer(serializers.ModelSerializer):
    create_date = serializers.DateTimeField(read_only=True, source='created_at')
    items = InvoiceItemSerializer(many=True,)

    class Meta:
        model = Invoice
        fields = ['id', 'customer', 'agent', 'create_date', 'due_date', 'total_amount', 'status', 'notes', 'image', 'items']
        
    def create(self, validated_data):
        items_data = json.loads(validated_data.pop('items'))
        invoice = Invoice.objects.create(**validated_data)
        for item in items_data:
            InvoiceItem.objects.create(invoice=invoice, **item)
        return invoice


# ------------------------------
# AdminInvoice Serializers
# ------------------------------

class AdminInvoiceItemSerializer(serializers.ModelSerializer):
    total = serializers.ReadOnlyField()

    class Meta:
        model = AdminInvoiceItem
        fields = ['id', 'description', 'qty', 'unit_price', 'total']


class AdminInvoiceListSerializer(serializers.ModelSerializer):
    create_date = serializers.DateTimeField(read_only=True, source='created_at')
    assigned_to_username = serializers.CharField(source='assigned_to.username', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = AdminInvoice
        fields = ['id', 'invoice_number', 'assigned_to_username', 'created_by_username', 'create_date', 'due_date', 'amount', 'status']


class AdminInvoiceDetailSerializer(serializers.ModelSerializer):
    create_date = serializers.DateTimeField(read_only=True, source='created_at')
    items = AdminInvoiceItemSerializer(many=True, read_only=True)
    assigned_to_username = serializers.CharField(source='assigned_to.username', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = AdminInvoice
        fields = ['id', 'invoice_number', 'assigned_to_username', 'created_by_username', 'create_date', 'due_date', 'description', 'amount', 'status', 'notes', 'items']
