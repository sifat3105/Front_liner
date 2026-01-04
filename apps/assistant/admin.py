from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from .models import (
    Assistant, AssistantFile, Transcript,
    TranscriptChunk, AssistantMamory
)


# =========================
# Assistant
# =========================
class AssistantFileInline(admin.TabularInline):
    model = AssistantFile
    extra = 0
    readonly_fields = ('created_at', 'updated_at')
    fields = ('file', 'created_at', 'updated_at')


@admin.register(Assistant)
class AssistantAdmin(UnfoldModelAdmin):
    list_display = ('id', 'name', 'owner', 'enabled', 'language', 'voice', 'model', 'created_at')
    list_filter = ('enabled', 'language', 'voice', 'model', 'created_at')
    search_fields = ('name', 'owner__username', 'voice')
    readonly_fields = ('public_id', 'created_at', 'updated_at')
    ordering = ('-created_at',)

    inlines = [AssistantFileInline]

    fieldsets = (
        ('Basic Info', {
            'fields': ('owner', 'name', 'description', 'avatar_url', 'enabled')
        }),
        ('Model & Language Settings', {
            'fields': ('model', 'language', 'voice', 'max_tokens', 'temperature', 'first_message_mode', 'first_message', 'system_prompt')
        }),
        ('UI & Theme', {
            'fields': ('theme_primary', 'embed_html')
        }),
        ('Twilio / ElevenLabs', {
            'fields': ('twilio_number', 'eleven_agent_id')
        }),
        ('Crisis Keywords', {
            'fields': ('crisis_keywords', 'crisis_keywords_prompt')
        }),
        ('Config & Metadata', {
            'fields': ('config', 'public_id', 'created_at', 'updated_at')
        }),
    )


# =========================
# Transcript
# =========================
class TranscriptChunkInline(admin.TabularInline):
    model = TranscriptChunk
    extra = 0
    readonly_fields = ('sender', 'text', 'chunk', 'audio', 'created_at', 'updated_at')
    fields = ('sender', 'text', 'chunk', 'audio', 'created_at', 'updated_at')


@admin.register(Transcript)
class TranscriptAdmin(UnfoldModelAdmin):
    list_display = ('id', 'assistant', 'type', 'ended_reason', 'successs_evalation', 'score', 'start_time', 'end_time', 'cost')
    list_filter = ('type', 'ended_reason', 'successs_evalation', 'start_time', 'end_time')
    search_fields = ('assistant__name', 'call_id')
    ordering = ('-start_time',)
    inlines = [TranscriptChunkInline]

    fieldsets = (
        ('Basic Info', {
            'fields': ('assistant', 'call_id', 'type', 'ended_reason')
        }),
        ('Evaluation & Cost', {
            'fields': ('successs_evalation', 'score', 'cost')
        }),
        ('Timestamps', {
            'fields': ('start_time', 'end_time', 'duration', 'created_at', 'updated_at')
        }),
    )


# =========================
# Transcript Chunk
# =========================
@admin.register(TranscriptChunk)
class TranscriptChunkAdmin(UnfoldModelAdmin):
    list_display = ('id', 'transcript', 'sender', 'created_at')
    list_filter = ('sender', 'created_at')
    search_fields = ('transcript__call_id', 'text')
    readonly_fields = ('created_at', 'updated_at', 'chunk')
    ordering = ('-created_at',)


# =========================
# Assistant Memory
# =========================
@admin.register(AssistantMamory)
class AssistantMamoryAdmin(UnfoldModelAdmin):
    list_display = ('id', 'assistant', 'updated_at')
    search_fields = ('assistant__name',)
    readonly_fields = ('updated_at',)
    ordering = ('-updated_at',)
