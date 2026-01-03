
from utils.base_view import BaseAPIView as APIView
from rest_framework import permissions
from .models import Order
from .serializers import OrderSerializer, OrderListSerializer

class OrderListAPIView(APIView):

    def get(self, request, *args, **kwargs):
        order_type = kwargs.get('type')

        status_map = {
            'confirm': 'CONFIRM',
            'reject': 'CANCEL',
            'list': 'PENDING',
        }

        orders = Order.objects.filter(
            user=request.user,
            order_status=status_map.get(order_type)
        ) if order_type in status_map else Order.objects.none()

        serializer = OrderListSerializer(orders, many=True)
        return self.success(data=serializer.data)
    
class OrderDetailAPIView(APIView):
    
    def get(self, request, order_id):
        if not Order.objects.filter(user=request.user, id=order_id).exists():
            return self.error(message="Order not found")
        order = Order.objects.prefetch_related('items').get(user=request.user, id=order_id)
        serializer = OrderSerializer(order, context={'request': request})
        return self.success(data=serializer.data)
    

    
