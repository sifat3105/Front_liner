from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from .models import SocialPost, SocialMedia, SocialPostPublish

@admin.register(SocialPost)
class SocialPostAdmin(UnfoldModelAdmin):
    list_display = ("id", "author", "title", "scheduled_at", "is_published", "created_at")
    list_filter = ("is_published", "scheduled_at", "created_at")
    search_fields = ("author__username", "title", "caption")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(SocialMedia)
class SocialMediaAdmin(UnfoldModelAdmin):
    list_display = ("id", "post", "media_type", "file", "created_at")
    list_filter = ("media_type", "created_at")
    search_fields = ("post__title", "post__author__username")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(SocialPostPublish)
class SocialPostPublishAdmin(UnfoldModelAdmin):
    list_display = ("id", "post", "platform", "status", "published_at", "created_at")
    list_filter = ("platform", "status", "published_at")
    search_fields = ("post__title", "post__author__username", "platform_post_id")
    readonly_fields = ("created_at", "published_at")
    ordering = ("-created_at",)
