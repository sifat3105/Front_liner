from django.urls import path
from .views import (
    PaperflyRegistrationAPIView,
    PaperflyOrderCreateAPIView,
    PaperflyOrderTrackingAPIView,
    PaperflyOrderCancelAPIView
)

urlpatterns = [
    # Merchant Registration API
    path('paperfly/register/', PaperflyRegistrationAPIView.as_view(), name='paperfly-register'),

    # Order Create API
    path('paperfly/order/create/', PaperflyOrderCreateAPIView.as_view(), name='paperfly-order-create'),

    # Order Tracking API
    path('paperfly/order/track/', PaperflyOrderTrackingAPIView.as_view(), name='paperfly-order-track'),

    # Order Cancellation API
    path("paperfly/order/cancel/", PaperflyOrderCancelAPIView.as_view(), name="paperfly-order-cancel"),
]

