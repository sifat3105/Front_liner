# apps/assistant/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponse
import csv

from .models import (
    Assistant, AssistantFile, Transcript, TranscriptChunk, AssistantMamory
)

# Try to use django-unfold if installed; otherwise fallback to plain admin classes.
try:
    from unfold.admin import UnfoldModelAdmin, UnfoldInline, TabbedInline
    UnfoldBase = UnfoldModelAdmin
    InlineBase = UnfoldInline
    TABBED_AVAILABLE = True
except Exception:
    UnfoldBase = admin.ModelAdmin
    InlineBase = admin.TabularInline
    TABBED_AVAILABLE = False


class AssistantFileInline(InlineBase):
    model = AssistantFile
    extra = 0
    readonly_fields = ("created_at", "updated_at")
    fields = ("file", "created_at", "updated_at")
    can_delete = True


class TranscriptChunkInline(InlineBase):
    model = TranscriptChunk
    extra = 0
    fields = ("sender", "text", "chunk", "audio", "created_at")
    readonly_fields = ("created_at", "updated_at")

from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils.html import format_html

from .models import Assistant


@admin.register(Assistant)
class AssistantAdmin(ModelAdmin):

    # -----------------------------
    # LIST PAGE CONFIG
    # -----------------------------
    list_display = (
        "name",
        "owner",
        "language",
        "model",
        "enabled_badge",
        "twilio_number",
        "updated_at",
    )

    search_fields = (
        "name",
        "owner__username",
        "owner__email",
        "twilio_number",
        "public_id",
    )

    list_filter = (
        "enabled",
        "language",
        "model",
        "first_message_mode",
        "updated_at",
    )

    ordering = ("-updated_at",)

    readonly_fields = ("public_id", "created_at", "updated_at")

    # -----------------------------
    # STATUS BADGES
    # -----------------------------
    def enabled_badge(self, obj):
        color = "#16a34a" if obj.enabled else "#dc2626"
        label = "Enabled" if obj.enabled else "Disabled"
        return format_html(
            '<span style="background:{}; color:white; padding:4px 10px; '
            'border-radius:6px; font-weight:600;">{}</span>',
            color,
            label,
        )

    enabled_badge.short_description = "Status"

    # -----------------------------
    # DETAIL PAGE UI (FIELDSETS)
    # -----------------------------
    fieldsets = (
        ("Basic Information", {
            "fields": (
                "owner",
                "name",
                "description",
                "enabled",
                "avatar_url",
            )
        }),

        ("Language & Voice", {
            "fields": (
                "language",
                "voice",
            )
        }),

        ("AI Model Configuration", {
            "fields": (
                "model",
                "max_tokens",
                "temperature",
                "system_prompt",
            )
        }),

        ("Messaging Behavior", {
            "fields": (
                "first_message_mode",
                "first_message",
            )
        }),

        ("Call Handling / Twilio", {
            "fields": (
                "twilio_number",
            )
        }),

        ("Crisis Mode (Optional)", {
            "fields": (
                "crisis_keywords",
                "crisis_keywords_prompt",
            )
        }),

        ("Visual Theme", {
            "fields": (
                "theme_primary",
            )
        }),

        ("Embedding / Frontend", {
            "fields": (
                "embed_html",
            )
        }),

        ("ElevenLabs (Optional)", {
            "fields": (
                "eleven_agent_id",
            )
        }),

        ("System Metadata", {
            "fields": (
                "public_id",
                "created_at",
                "updated_at",
            )
        }),
    )



@admin.register(Transcript)
class TranscriptAdmin(UnfoldBase):
    list_display = ("id", "assistant", "type", "call_id", "start_time", "end_time", "duration_display", "score", "cost")
    list_filter = ("type", "ended_reason", "assistant__name")
    search_fields = ("call_id", "assistant__name")
    readonly_fields = ("call_id", "start_time", "end_time", "cost")
    inlines = [TranscriptChunkInline]

    if TABBED_AVAILABLE:
        unfold_tabs = [
            ("Overview", {"fields": ["assistant", "type", "ended_reason", "call_id", "score", "successs_evalation"]}),
            ("Timing & Cost", {"fields": ["start_time", "end_time", "cost"]}),
        ]
    else:
        fieldsets = (
            (None, {"fields": ("assistant", "type", "ended_reason", "call_id")}),
            ("Evaluation", {"fields": ("successs_evalation", "score")}),
            ("Timing & Cost", {"fields": ("start_time", "end_time", "cost")}),
        )

    def duration_display(self, obj):
        return obj.duration
    duration_display.short_description = "Duration"


@admin.register(TranscriptChunk)
class TranscriptChunkAdmin(admin.ModelAdmin):
    list_display = ("id", "transcript", "sender", "short_text", "created_at")
    list_filter = ("sender",)
    search_fields = ("text", "chunk", "transcript__call_id")
    readonly_fields = ("created_at", "updated_at")

    def short_text(self, obj):
        t = obj.text or obj.chunk or ""
        return (t[:100] + "...") if len(t) > 100 else t
    short_text.short_description = "Text"


@admin.register(AssistantMamory)
class AssistantMamoryAdmin(admin.ModelAdmin):
    list_display = ("id", "assistant", "updated_at")
    readonly_fields = ("updated_at",)
    search_fields = ("assistant__name",)
