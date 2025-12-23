from django.urls import path
from .views import (
    InitiatePaymentAPIView,
    PaymentCallbackAPIView,
    TransactionStatusAPIView,
    TransactionStatusByTrxAPIView,
)

urlpatterns = [
    path('initiate/', InitiatePaymentAPIView.as_view()),
    path('callback/', PaymentCallbackAPIView.as_view()),
    path('status/', TransactionStatusAPIView.as_view()),
    path('status-by-trx/', TransactionStatusByTrxAPIView.as_view()),
]
