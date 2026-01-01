from django.urls import path
from .views import (
    IncomeAPIView, PaymentAPIView,
    CustomerRefundListAPIView,
    CustomerSellsListAPIView,
    DebitCreditReportAPIView,
    ProfitLossReportAPIView,
    ReceiverListCreateAPIView, ReceiverListCreateAPIView, InvoiceListCreateAPIView, PaymentCreateAPIView
)

urlpatterns = [
    path('income/', IncomeAPIView.as_view(), name='income-list'),
    path('payments/', PaymentAPIView.as_view(), name='payment-list'),

    # Refund
    path('sells/', CustomerSellsListAPIView.as_view(), name='sell-list'),
    path('refund/', CustomerRefundListAPIView.as_view(), name='refund-list'),

    # Debit Credit
    path('debit-credit/report/', DebitCreditReportAPIView.as_view()),


    # Profit & Loss (P&L) sectiont
    path('profit-loss/',ProfitLossReportAPIView.as_view(),name='profit-loss-api'),

    # Payment section
    path('payment/', PaymentCreateAPIView.as_view(), name='payment-create'),

    # Receiver APIs
    path('receivers/', ReceiverListCreateAPIView.as_view(), name='receiver-list-create'),

    # Product APIs
    path('products/', ReceiverListCreateAPIView.as_view(), name='product-list-create'),

    # Invoice APIs
    path('invoices/', InvoiceListCreateAPIView.as_view(), name='invoice-list-create'),
]

