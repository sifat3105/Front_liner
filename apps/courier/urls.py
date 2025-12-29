from django.urls import path
from .views import (
    PaperflyRegistrationAPIView,
    PaperflyOrderCreateAPIView,
    PaperflyOrderTrackingAPIView,
    PaperflyOrderCancelAPIView,

    # STEADFAST
    PlaceOrderAPIView,
    BulkOrderAPIView,
    DeliveryStatusByCIDAPIView,
    DeliveryStatusByInvoiceAPIView,
    DeliveryStatusByTrackingCodeAPIView,
    CurrentBalanceAPIView,
    ReturnRequestAPIView,
    GetReturnRequestsAPIView,
    GetPaymentsAPIView,
    GetSinglePaymentAPIView,
    GetPoliceStationsAPIView,

    # PATHAO
    PathaoIssueTokenAPIView,
    PathaoRefreshTokenAPIView,
    PathaoCreateStoreAPIView,
    PathaoCreateOrderAPIView,
    PathaoBulkOrderAPIView,
    PathaoOrderInfoAPIView,
    PathaoCityListAPIView,
    PathaoZoneListAPIView,
    PathaoAreaListAPIView,
    PathaoPricePlanAPIView,
    PathaoStoreListAPIView,
)

urlpatterns = [
    # Merchant Registration API
    path('paperfly/register/', PaperflyRegistrationAPIView.as_view(), name='paperfly-register'),

    # Order Create API
    path('paperfly/order/create/', PaperflyOrderCreateAPIView.as_view(), name='paperfly-order-create'),

    # Order Tracking API
    path('paperfly/order/track/', PaperflyOrderTrackingAPIView.as_view(), name='paperfly-order-track'),

    # Order Cancellation API
    path("paperfly/order/cancel/", PaperflyOrderCancelAPIView.as_view(), name="paperfly-order-cancel"),

    # ===============================
    # STEADFAST APIs
    # ===============================
    path("steadfast/order/create/", PlaceOrderAPIView.as_view(), name="steadfast-create-order"),
    path("steadfast/order/bulk/", BulkOrderAPIView.as_view(), name="steadfast-bulk-order"),

    path("steadfast/status/cid/<str:consignment_id>/", DeliveryStatusByCIDAPIView.as_view(),name="steadfast-status-by-cid"),
    path("steadfast/status/invoice/<str:invoice>/", DeliveryStatusByInvoiceAPIView.as_view(),name="steadfast-status-by-invoice"),
    path("steadfast/status/tracking/<str:tracking_code>/", DeliveryStatusByTrackingCodeAPIView.as_view(),name="steadfast-status-by-tracking"),

    path("steadfast/balance/", CurrentBalanceAPIView.as_view(), name="steadfast-balance"),

    path("steadfast/return/create/", ReturnRequestAPIView.as_view(), name="steadfast-return-create"),
    path("steadfast/return/list/", GetReturnRequestsAPIView.as_view(), name="steadfast-return-list"),

    path("steadfast/payments/", GetPaymentsAPIView.as_view(), name="steadfast-payments"),
    path("steadfast/payments/<int:payment_id>/", GetSinglePaymentAPIView.as_view(),name="steadfast-single-payment"),

    path("steadfast/police-stations/", GetPoliceStationsAPIView.as_view(),name="steadfast-police-stations"),

    # ===============================
    # PATHAO APIs
    # ===============================
    path("pathao/token/issue/", PathaoIssueTokenAPIView.as_view(), name="pathao-issue-token"),
    path("pathao/token/refresh/", PathaoRefreshTokenAPIView.as_view(), name="pathao-refresh-token"),

    path("pathao/store/create/", PathaoCreateStoreAPIView.as_view(), name="pathao-create-store"),
    path("pathao/store/list/", PathaoStoreListAPIView.as_view(), name="pathao-store-list"),

    path("pathao/order/create/", PathaoCreateOrderAPIView.as_view(), name="pathao-create-order"),
    path("pathao/order/bulk/", PathaoBulkOrderAPIView.as_view(), name="pathao-bulk-order"),
    path("pathao/order/info/<str:consignment_id>/", PathaoOrderInfoAPIView.as_view(),
         name="pathao-order-info"),

    path("pathao/location/cities/", PathaoCityListAPIView.as_view(), name="pathao-city-list"),
    path("pathao/location/zones/<int:city_id>/", PathaoZoneListAPIView.as_view(),
         name="pathao-zone-list"),
    path("pathao/location/areas/<int:zone_id>/", PathaoAreaListAPIView.as_view(),
         name="pathao-area-list"),

    path("pathao/price/calculate/", PathaoPricePlanAPIView.as_view(), name="pathao-price-plan"),
]