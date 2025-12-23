"""
URL configuration for project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
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


    path("connect-facebook/", connect_facebook_page),
    path("post-generate/", post_generate),
    path("api/",include('apps.user.urls')),
    path("api/",include('apps.account.urls')),
    path("api/",include('apps.sells.urls')),
    path("api/",include('apps.courier.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
