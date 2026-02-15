from rest_framework import serializers
from .models import Order, OrderItem

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product_name', 'product_image', 'quantity', 'color', 'size', 'weight', 'notes']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    call_confirmation_status = serializers.SerializerMethodField()


    class Meta:
        model = Order
        fields = ['id', 'order_id', 'customer', 'location', 'contact', 'order_amount', 'platform', 'status', 'order_status', 'call_confirmation_status', 'items', ]

    def get_action(self, obj):
        return obj.get_view_action()

    def get_call_confirmation_status(self, obj):
        confirmation = getattr(obj, "call_confirmation", None)
        return confirmation.status if confirmation else "PENDING"
    
class OrderListSerializer(serializers.ModelSerializer):
    call_confirmation_status = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'order_id', 'customer', 'location', 'contact', 'order_amount', 'platform', 'status', 'order_status', 'call_confirmation_status']

    def get_action(self, obj):
        return obj.get_view_action()

    def get_call_confirmation_status(self, obj):
        confirmation = getattr(obj, "call_confirmation", None)
        return confirmation.status if confirmation else "PENDING"
