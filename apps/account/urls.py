from django.urls import path
from .views import (
    IncomeAPIView,
    CustomerRefundListAPIView,
    CustomerSellsListAPIView,
    DebitCreditReportAPIView,
    ProfitLossReportAPIView,
    PaymentAPIView
)

urlpatterns = [
    path('income/', IncomeAPIView.as_view(), name='income-list'),

    # Refund
    path('sells/', CustomerSellsListAPIView.as_view(), name='sell-list'),
    path('refund/', CustomerRefundListAPIView.as_view(), name='refund-list'),

    # Debit Credit
    path('debit-credit/report/', DebitCreditReportAPIView.as_view()),


    # Profit & Loss (P&L) sectiont
    path('profit-loss/',ProfitLossReportAPIView.as_view(),name='profit-loss-api'),

    # Payment section
    path('payment/create/', PaymentAPIView.as_view(), name='payment-create'),
    
    path('payment/list/', PaymentAPIView.as_view(), name='payment-list'),
]

