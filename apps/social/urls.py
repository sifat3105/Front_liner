from django.urls import path
from .views import (SocialConnectURL, FacebookCallback, FacebookPageListView, FacebookWebhook, 
                    MessangerConnectWithBot, SocialPlatformListView, TikTokConnectURL, FacebookDeletion,
                    InstagramCallback, MetaDataDeletionAPIView, WhatsappCallback, TikTokCallback,
                    InstagramWebhook, TikTokWebhook, WhatsAppBusinessAccountListView
                )

urlpatterns = [
    path("meta_data_deletion/", MetaDataDeletionAPIView.as_view()),
    path("platforms/", SocialPlatformListView.as_view()),
    path("tiktok/connect/", TikTokConnectURL.as_view()),
    path("<str:platform>/connect/", SocialConnectURL.as_view()),
    path("facebook/callback/", FacebookCallback.as_view()),
    path("instagram/callback/", InstagramCallback.as_view()),
    path("tiktok/callback/", TikTokCallback.as_view()),
    path("facebook/pages/", FacebookPageListView.as_view()),
    path("whatsapp/accounts/", WhatsAppBusinessAccountListView.as_view()),
    path("facebook/delete/", FacebookDeletion.as_view()),
    path("whatsapp/callback/", WhatsappCallback.as_view()),
    path("facebook/messanger_connect_with_bot/", MessangerConnectWithBot.as_view()),
    
    #webhook
    path("facebook/webhook/", FacebookWebhook.as_view()),
    path("instagram/webhook/", InstagramWebhook.as_view()),
    path("tiktok/webhook/", TikTokWebhook.as_view()),
    
]
