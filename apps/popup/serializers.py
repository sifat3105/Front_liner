from rest_framework import serializers
from decimal import Decimal
from .models import Wallet #Recharge


# class WalletSerializer(serializers.ModelSerializer):
#     balance = serializers.DecimalField(
#         max_digits=12,
#         decimal_places=2,
#         read_only=True
#     )

#     class Meta:
#         model = Wallet
#         fields = (
#             "balance",
#             "message",
#             "updated_at",
#         )


# class RechargeCreateSerializer(serializers.Serializer):
#     amount = serializers.DecimalField(
#         max_digits=10,
#         decimal_places=2,
#         min_value=Decimal("1.00")
#     )

#     def validate_amount(self, value):
#         if value <= 0:
#             raise serializers.ValidationError(
#                 "Recharge amount must be greater than zero."
#             )

#         if value > Decimal("100000"):
#             raise serializers.ValidationError(
#                 "Recharge amount exceeds allowed limit."
#             )

#         return value


# class RechargeStatusSerializer(serializers.Serializer):
#     balance = serializers.DecimalField(
#         max_digits=12,
#         decimal_places=2
#     )
#     recharge_required = serializers.BooleanField()
#     reason = serializers.CharField(allow_null=True)



class WalletPopupSerializer(serializers.ModelSerializer):
    show_popup = serializers.SerializerMethodField()

    class Meta:
        model = Wallet
        fields = (
            "balance",
            "show_popup",
            "message",
        )

    def get_show_popup(self, obj):
        """
        BUSINESS LOGIC:
        - balance <= 0  → popup show
        - balance > 0   → popup hide
        """
        return obj.balance <= Decimal("0.00")
