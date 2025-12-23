from django.contrib import admin
from .models import SocialPost, SocialMedia, SocialPostPublish

admin.site.register(SocialPost)
admin.site.register(SocialMedia)
admin.site.register(SocialPostPublish)
