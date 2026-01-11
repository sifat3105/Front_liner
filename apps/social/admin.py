from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from .models import SocialPlatform, SocialAccount, FacebookPage, InstagramAccount

@admin.register(SocialPlatform)
class SocialPlatformAdmin(UnfoldModelAdmin):
    list_display = ("id", "display_name", "name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "display_name")
    ordering = ("-created_at",)

@admin.register(SocialAccount)
class SocialAccountAdmin(UnfoldModelAdmin):
    list_display = ("id", "user", "platform", "name", "created_at")
    list_filter = ("platform",)
    search_fields = ("user__username", "name", "platform")
    ordering = ("-created_at",)

@admin.register(FacebookPage)
class FacebookPageAdmin(UnfoldModelAdmin):
    list_display = ("id", "page_name", "social_account", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("page_name", "social_account__user__username")
    ordering = ("-created_at",)
    
@admin.register(InstagramAccount)
class InstagramAccountAdmin(UnfoldModelAdmin):
    list_display = ("id", "username", "name", "profile_picture", "page_id", "page_access_token", "created_at")
    list_filter = ("is_active",)
    search_fields = ("username", "name", "profile_picture", "page_id")
    ordering = ("-created_at",)
