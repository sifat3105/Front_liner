from django.urls import path
from .views import FacebookConnectURL, FacebookCallback, FacebookPageListView

urlpatterns = [
    path("facebook/connect/", FacebookConnectURL.as_view()),
    path("facebook/callback/", FacebookCallback.as_view()),
    path("facebook/pages/", FacebookPageListView.as_view()),
]