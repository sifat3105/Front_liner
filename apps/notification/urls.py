from django.urls import path
from . import views

urlpatterns = [
    path("notification/", views.NotificationView.as_view(), name="notification"),
]