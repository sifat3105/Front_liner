
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from .views import connect_facebook_page, post_generate

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/", include("apps.user.urls")),
    path("api/social/", include("apps.social.urls")),
    path("api/publish/", include("apps.publish.urls")),
    path("api/post/", include("apps.post.urls")),
    path("api/chat/", include("apps.chat.urls")),


    path("connect-facebook/", connect_facebook_page),
    path("post-generate/", post_generate),
    path("api/",include('apps.user.urls')),
    path("api/",include('apps.account.urls')),
    path("api/",include('apps.sells.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
