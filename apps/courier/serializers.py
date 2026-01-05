from rest_framework import serializers
from .models import CourierList, CourierOrder, CourierOrderStatus

class CourierCompanySerializer(serializers.ModelSerializer):
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = CourierList
        fields = ['id', 'name', 'logo', 'is_active', 'created_at', 'updated_at']
        
    def get_is_active(self, obj):
        user_couriers = self.context.get('user_couriers', [])
        for uc in user_couriers:
            if uc.courier_id == obj.id:
                return uc.is_active
        return False

class OrderCourierStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourierOrderStatus
        fields = ['id', 'status', 'status_time']
        
class CourierOrderSerializer(serializers.ModelSerializer):
    courier = serializers.SerializerMethodField()
    customer = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    order_id = serializers.SerializerMethodField()
    courier_status = OrderCourierStatusSerializer(source='track_status', many=True)

    class Meta:
        model = CourierOrder
        fields = ['id', 'order_id', 'courier', 'customer', 'price', 'status', 'courier_status']
        
    def get_courier(self, obj):
        return obj.courier.name
    
    def get_customer(self, obj):
        return obj.order.customer
    
    def get_price(self, obj):
        return obj.order.order_amount
    
    def get_status(self, obj):
        last_status = obj.track_status.last()
        return last_status.status if last_status else None
    
    def get_order_id(self, obj):
        return obj.order.order_id