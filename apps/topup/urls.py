from django.urls import path
from . import views
urlpatterns = [
    path("topup/", views.TopupView.as_view(), name="topup"),
    path("topup/webhook", views.PaymentWebhookView.as_view(), name="topup-webhook"),
]