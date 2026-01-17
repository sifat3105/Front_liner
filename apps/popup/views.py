# wallet/views.py
from utils.base_view import BaseAPIView as APIView
from rest_framework.permissions import IsAuthenticated
from django.db import transaction

from .models import Wallet #, Recharge
# from .serializers import (
#     WalletSerializer,
#     RechargeCreateSerializer,
#     RechargeStatusSerializer
# )
# from .models import is_recharge_popup_required


from .serializers import WalletPopupSerializer


class WalletPopupAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet, _ = Wallet.objects.get_or_create(user=request.user)

        serializer = WalletPopupSerializer(wallet)

        return self.success(
            message="Wallet popup status",
            data=serializer.data
        )


# --------------------------------
# Recharge Status API
# --------------------------------
# class RechargeStatusAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         wallet, _ = Wallet.objects.get_or_create(user=request.user)

#         show_popup, reason = is_recharge_popup_required(wallet)

#         serializer = RechargeStatusSerializer({
#             "balance": wallet.balance,
#             "recharge_required": show_popup,
#             "reason": reason
#         })

#         return self.success(
#             message="Recharge status fetched successfully",
#             data=serializer.data
#         )


# --------------------------------
# Recharge API
# --------------------------------
# class RechargeAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         serializer = RechargeCreateSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         amount = serializer.validated_data["amount"]

#         with transaction.atomic():
#             wallet, _ = Wallet.objects.select_for_update().get_or_create(
#                 user=request.user
#             )

#             wallet.balance += amount
#             wallet.save(update_fields=["balance", "updated_at"])

#             Recharge.objects.create(
#                 user=request.user,
#                 amount=amount,
#                 is_success=True
#             )

#         wallet_serializer = WalletSerializer(wallet)

#         return self.success(
#             message="Recharge completed successfully",
#             data=wallet_serializer.data
#         )
