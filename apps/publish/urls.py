from django.urls import path
from .views import (SocialPostView, SocialMediaGalleryView, SocialPostPublishView
                    ,PlatformPageListView, SocialPlatformListView
                    )

urlpatterns = [
    path("post/", SocialPostView.as_view()),
    path("media/", SocialMediaGalleryView.as_view()),
    path("publish/", SocialPostPublishView.as_view()),
    path("pages/", PlatformPageListView.as_view()),
    path("platforms/", SocialPlatformListView.as_view()),
]