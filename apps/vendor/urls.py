from django.urls import path
from .views import VendorRegistrationAPIView

urlpatterns = [
    path('vendors/register/',VendorRegistrationAPIView.as_view(),name='vendor-register'),
]
