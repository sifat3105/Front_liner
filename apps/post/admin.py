from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from .models import GeneratedCaption

@admin.register(GeneratedCaption)
class GeneratedCaptionAdmin(UnfoldModelAdmin):
    list_display = (
        "author",
        "platform",
        "tone",
        "topic",
        "call_to_action",
        "character_count",
        "word_count",
        "within_limit",
        "created_at",
        "updated_at",
    )
    list_filter = ("platform", "tone", "within_limit", "created_at")
    search_fields = ("author__username", "topic", "call_to_action", "description")
    readonly_fields = ("created_at", "updated_at", "character_count", "word_count", "within_limit")
    ordering = ("-created_at",)
