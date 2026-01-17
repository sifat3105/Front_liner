# from django.contrib import admin
# from .models import Wallet, Recharge

# # Register your models here.


# @admin.register(Wallet)
# class WalletAdmin(admin.ModelAdmin):
#     list_display = (
#         "user",
#         "balance",
#         "updated_at",
#     )
#     search_fields = ("user__email", "user__username")
#     readonly_fields = ("updated_at",)
#     list_select_related = ("user",)


# @admin.register(Recharge)
# class RechargeAdmin(admin.ModelAdmin):
#     list_display = (
#         "user",
#         "amount",
#         "is_success",
#         "created_at",
#     )
#     list_filter = ("is_success", "created_at")
#     search_fields = ("user__email", "user__username")
#     readonly_fields = ("created_at",)
#     list_select_related = ("user",)


# wallet/admin.py
from django.contrib import admin
from .models import Wallet

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("user", "balance", "updated_at")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("updated_at",)
