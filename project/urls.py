
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from .views import connect_facebook_page, post_generate, login

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/", include("apps.user.urls")),
    path("api/social/", include("apps.social.urls")),
    path("api/publish/", include("apps.publish.urls")),
    path("api/post/", include("apps.post.urls")),
    path("api/chat/", include("apps.chat.urls")),
    
    # CareOn Project URLs
    path("api/voice/", include("apps.voice.urls")),
    path("api/assistant/", include("apps.assistant.urls")),
    path("api/support/", include("apps.support.urls")),
    path("api/call/", include("apps.call.urls")),
    path("api/invoice/", include("apps.invoice.urls")),
    path("api/phone_number/", include("apps.phone_number.urls")),
    path("api/transaction/", include("apps.transaction.urls")),
    path("api/topup/", include("apps.topup.urls")),
    path("api/notification/", include("apps.notification.urls")),
    
    


    path("connect-facebook/", connect_facebook_page),
    path("post-generate/", post_generate),
    path("login/", login),
    path("api/",include('apps.account.urls')),
    path("api/",include('apps.sells.urls')),
    path("api/",include('apps.courier.urls')),
    path("api/",include('apps.paymentgateway.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
