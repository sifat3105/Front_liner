from django.urls import path
from .views import (SocialPostView, SocialMediaGalleryView, SocialPostPublishView
                    ,PlatformPageListView, SocialPlatformListView, SocialPostdetailView, GeneratePostCaption
                    )

urlpatterns = [
    path("generate/<str:name>/", GeneratePostCaption.as_view()),
    path("post/", SocialPostView.as_view()),
    path("post/<int:post_id>/", SocialPostdetailView.as_view()),
    path("media/", SocialMediaGalleryView.as_view()),
    path("publish/", SocialPostPublishView.as_view()),
    path("pages/", PlatformPageListView.as_view()),
    path("platforms/", SocialPlatformListView.as_view()),
]