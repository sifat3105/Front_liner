from django.urls import path
from .views import VendorRegistrationAPIView,VendorListAPIView

urlpatterns = [
    path('vendors/register/',VendorRegistrationAPIView.as_view(),name='vendor-register'),
    path('list/vendors/', VendorListAPIView.as_view(), name='vendor-list'),
]
