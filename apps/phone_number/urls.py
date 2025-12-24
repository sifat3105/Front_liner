from django.urls import path
from .views import AvailbePhoneNumberView, PhoneNumberView, PurchasePhoneNumberView, CountryView

urlpatterns = [
    path('available/', AvailbePhoneNumberView.as_view(), name='phone-number-available'),
    path('purchase/', PurchasePhoneNumberView.as_view(), name='phone-number-purchase'),
    path('list/', PhoneNumberView.as_view(), name='phone-number-list'),
    path('countries/', CountryView.as_view(), name='phone-number-countries'),
]   