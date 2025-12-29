from django.contrib import admin
from .models import SocialAccount, FacebookPage, SocialPlatform

admin.site.register(SocialAccount)
admin.site.register(FacebookPage)
admin.site.register(SocialPlatform)
