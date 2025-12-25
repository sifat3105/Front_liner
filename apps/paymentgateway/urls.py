from django.urls import path
from .views import (
    InitiatePaymentAPIView,
    PaymentCallbackAPIView,
    TransactionStatusAPIView,
    TransactionStatusByTrxAPIView,
    ShurjopayPaymentAPIView,
    ShurjopayReturnAPIView,
    ShurjopayCancelAPIView,
)

urlpatterns = [
    path('initiate/', InitiatePaymentAPIView.as_view()),
    path('callback/', PaymentCallbackAPIView.as_view()),
    path('status/', TransactionStatusAPIView.as_view()),
    path('status-by-trx/', TransactionStatusByTrxAPIView.as_view()),

    # shurjopay API
    path('shurjopay/initiate/', ShurjopayPaymentAPIView.as_view(), name='shurjopay-initiate'),
    path("payment/return/", ShurjopayReturnAPIView.as_view(),name="payment-return"),
    path("payment/cancel/", ShurjopayCancelAPIView.as_view(),name="payment-cancel"),

]