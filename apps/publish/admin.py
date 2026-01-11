from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from .models import SocialPost, PostMediaFile, MediaDraft

@admin.register(SocialPost)
class SocialPostAdmin(UnfoldModelAdmin):
    list_display = ("id", "author", "title", "scheduled_at", "is_published", "created_at")
    list_filter = ("is_published", "scheduled_at", "created_at")
    search_fields = ("author__username", "title", "caption")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(PostMediaFile)
class SocialMediaAdmin(UnfoldModelAdmin):
    list_display = ("id", "post", "media_type", "file", "created_at")
    list_filter = ("media_type", "created_at")
    search_fields = ("post__title", "post__author__username")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

@admin.register(MediaDraft)
class MediaDraftAdmin(UnfoldModelAdmin):
    list_display = ("id", "user", "media_type", "file", "created_at")
    list_filter = ("media_type", "created_at")
    search_fields = ("user__username", "file")
    readonly_fields = ("created_at", "updated_at")      

