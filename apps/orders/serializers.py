from rest_framework import serializers
from .models import Order, OrderItem

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product_name', 'product_image', 'quantity', 'color', 'size', 'weight', 'notes']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)


    class Meta:
        model = Order
        fields = ['id', 'order_id', 'customer', 'location', 'contact', 'order_amount', 'platform', 'status', 'items', ]

    def get_action(self, obj):
        return obj.get_view_action()
    
class OrderListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'order_id', 'customer', 'location', 'contact', 'order_amount', 'platform', 'status']

    def get_action(self, obj):
        return obj.get_view_action()
