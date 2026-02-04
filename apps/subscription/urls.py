from django.urls import path
from .views import (
    MySubscriptionView,
    SubscriptionPlanListView,
    SubscriptionPlanDetailView,
    SubscriptionPlanCreateView,
    SubscriptionPlanUpdateView,
    PurchaseSubscriptionView,
)

urlpatterns = [
    path("me/", MySubscriptionView.as_view(), name="my-subscription"),
    path("plans/", SubscriptionPlanListView.as_view(), name="subscription-plan-list"),
    path("plans/<int:plan_id>/", SubscriptionPlanDetailView.as_view(), name="subscription-plan-detail"),
    path("plans/create/", SubscriptionPlanCreateView.as_view(), name="subscription-plan-create"),
    path("plans/<int:plan_id>/update/", SubscriptionPlanUpdateView.as_view(), name="subscription-plan-update"),
    path("purchase/", PurchaseSubscriptionView.as_view(), name="subscription-purchase"),
]
