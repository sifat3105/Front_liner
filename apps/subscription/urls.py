from django.urls import path
from .views import (
    MySubscriptionView,
    SubscriptionPlanListView,
    SubscriptionPlanDetailView,
    PurchaseSubscriptionView,
)

urlpatterns = [
    path("me/", MySubscriptionView.as_view(), name="my-subscription"),
    path("plans/", SubscriptionPlanListView.as_view(), name="subscription-plan-list"),
    path("plans/<int:plan_id>/", SubscriptionPlanDetailView.as_view(), name="subscription-plan-detail"),
    path("purchase/", PurchaseSubscriptionView.as_view(), name="subscription-purchase"),
]
