from django.urls import path
from .views import (FacebookConnectURL, FacebookCallback, FacebookPageListView, FacebookWebhook, 
                    MessangerConnectWithBot, SocialPlatformListView, TikTokConnectURL, FacebookDeletion
                )

urlpatterns = [
    path("platforms/", SocialPlatformListView.as_view()),
    path("facebook/connect/", FacebookConnectURL.as_view()),
    path("tiktok/connect/", TikTokConnectURL.as_view()),
    path("facebook/callback/", FacebookCallback.as_view()),
    path("facebook/pages/", FacebookPageListView.as_view()),
    path("facebook/delete/", FacebookDeletion.as_view()),
    path("whatsapp/callback/", FacebookCallback.as_view()),
    
    path("facebook/messanger_connect_with_bot/", MessangerConnectWithBot.as_view()),
    
    #webhook
    path("facebook/webhook/", FacebookWebhook.as_view()),
    
]