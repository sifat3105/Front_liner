from django.urls import path

from .views import OrderCallConfirmationAPIView, OrderDetailAPIView, OrderListAPIView

urlpatterns = [
    path('<int:order_id>/call-confirmation/', OrderCallConfirmationAPIView.as_view(), name='order-call-confirmation'),
    path('<str:type>/', OrderListAPIView.as_view(), name='orders-list'),
    path('<int:order_id>/details/', OrderDetailAPIView.as_view(), name='orders-details'),
]
