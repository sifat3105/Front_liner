from django.urls import path
from .views import VendorRegistrationAPIView,VendorListAPIView,VendorPaymentHistoryAPIView,VendorDueListAPIView,VendorDetailUpdateAPIView

urlpatterns = [
    path('vendors/register/',VendorRegistrationAPIView.as_view(),name='vendor-register'),
    path('list/vendors/', VendorListAPIView.as_view(), name='vendor-list'),
    path('update/vendors/<int:vendor_id>/', VendorDetailUpdateAPIView.as_view(), name='update-vendor'),
    
    path('vendors/payments/history/', VendorPaymentHistoryAPIView.as_view(),name='payments-history'),
    path('vendors/payments/due/', VendorDueListAPIView.as_view(),name='payments-due'),
]
