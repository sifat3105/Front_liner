from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from .models import (
    CourierList, UserCourier,
    PaperflyMerchant, PaperflyOrder, PaperflyOrderTracking, PaperflyOrderCancel,
    SteadfastOrder, SteadfastTracking, SteadfastReturnRequest,
    PathaoToken, PathaoStore, PathaoOrder
)

# =========================
# Courier List
# =========================
@admin.register(CourierList)
class CourierListAdmin(UnfoldModelAdmin):
    list_display = ("name", "is_active", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    readonly_fields = ("created_at", "updated_at")
    ordering = ("name",)

# =========================
# User Courier
# =========================
@admin.register(UserCourier)
class UserCourierAdmin(UnfoldModelAdmin):
    list_display = ("user", "courier", "is_active", "created_at", "updated_at")
    list_filter = ("is_active", "courier")
    search_fields = ("user__username", "courier__name")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("user",)

# =========================
# Paperfly Merchant
# =========================
@admin.register(PaperflyMerchant)
class PaperflyMerchantAdmin(UnfoldModelAdmin):
    list_display = ("merchant_name", "district", "contact_name", "contact_number", "payment_mode", "created_at")
    search_fields = ("merchant_name", "district", "contact_name")
    readonly_fields = ("created_at",)
    ordering = ("merchant_name",)

# =========================
# Paperfly Order
# =========================
@admin.register(PaperflyOrder)
class PaperflyOrderAdmin(UnfoldModelAdmin):
    list_display = ("merOrderRef", "merchantCode", "custname", "custPhone", "created_at")
    search_fields = ("merOrderRef", "merchantCode", "custname")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)

# =========================
# Paperfly Tracking
# =========================
@admin.register(PaperflyOrderTracking)
class PaperflyOrderTrackingAdmin(UnfoldModelAdmin):
    list_display = ("ReferenceNumber", "merchantCode", "Delivered", "Returned", "close", "created_at")
    search_fields = ("ReferenceNumber", "merchantCode")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)

# =========================
# Paperfly Cancel
# =========================
@admin.register(PaperflyOrderCancel)
class PaperflyOrderCancelAdmin(UnfoldModelAdmin):
    list_display = ("order_id", "merchantCode", "response_code", "created_at")
    search_fields = ("order_id", "merchantCode")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)

# =========================
# Steadfast Order
# =========================
@admin.register(SteadfastOrder)
class SteadfastOrderAdmin(UnfoldModelAdmin):
    list_display = ("invoice", "consignment_id", "recipient_name", "cod_amount", "status", "created_at")
    search_fields = ("invoice", "consignment_id", "recipient_name")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

# =========================
# Steadfast Tracking
# =========================
@admin.register(SteadfastTracking)
class SteadfastTrackingAdmin(UnfoldModelAdmin):
    list_display = ("invoice", "consignment_id", "tracking_code", "delivery_status", "created_at")
    search_fields = ("invoice", "consignment_id", "tracking_code")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

# =========================
# Steadfast Return Request
# =========================
@admin.register(SteadfastReturnRequest)
class SteadfastReturnRequestAdmin(UnfoldModelAdmin):
    list_display = ("return_id", "invoice", "consignment_id", "status", "created_at")
    search_fields = ("return_id", "invoice", "consignment_id")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

# =========================
# Pathao Token
# =========================
@admin.register(PathaoToken)
class PathaoTokenAdmin(UnfoldModelAdmin):
    list_display = ("id", "expires_in", "created_at")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)

# =========================
# Pathao Store
# =========================
@admin.register(PathaoStore)
class PathaoStoreAdmin(UnfoldModelAdmin):
    list_display = ("store_id", "store_name", "city_id", "zone_id", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("store_id", "store_name")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("store_name",)

# =========================
# Pathao Order
# =========================
@admin.register(PathaoOrder)
class PathaoOrderAdmin(UnfoldModelAdmin):
    list_display = ("merchant_order_id", "consignment_id", "store", "order_status", "delivery_fee", "created_at")
    search_fields = ("merchant_order_id", "consignment_id", "store__store_name")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)
