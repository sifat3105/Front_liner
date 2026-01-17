# wallet/urls.py
# from django.urls import path
# from .views import RechargeAPIView, RechargeStatusAPIView

# urlpatterns = [
#     path("recharge/status/", RechargeStatusAPIView.as_view(), name="recharge-status"),
#     path("recharge/", RechargeAPIView.as_view(), name="recharge"),
# ]
# wallet/urls.py
from django.urls import path
from .views import WalletPopupAPIView

urlpatterns = [
    path("wallet/popup/", WalletPopupAPIView.as_view(), name="wallet-popup"),
]
