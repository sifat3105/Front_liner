from django.urls import path
from .views import OrderListAPIView, OrderDetailAPIView

urlpatterns = [
    path('<str:type>/', OrderListAPIView.as_view(), name='orders-list'),
    path('<int:order_id>/details/', OrderDetailAPIView.as_view(), name='orders-details'),
]