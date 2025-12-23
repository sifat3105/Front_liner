from django.urls import path
from .views import InvoiceListView, InvoiceDetailView
from .views import BillingInvoiceView, BillingInvoiceDetailView

urlpatterns = [
    path('invoices/', InvoiceListView.as_view(), name='invoice-list'),
    path('invoices/create/', InvoiceListView.as_view(), name='invoice-create'),
    path('invoices/<int:pk>/', InvoiceDetailView.as_view(), name='invoice-detail'),
    path('billing/invoices/', BillingInvoiceView.as_view(), name='billing-invoice-list'),
    path('billing/invoices/<int:pk>/', BillingInvoiceDetailView.as_view(), name='billing-invoice-detail'),
]