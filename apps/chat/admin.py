from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from .models import Conversation, Message

# =========================
# Message Inline
# =========================
class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = (
        "platform", "message_id", "sender_type",
        "text", "attachment_url", "is_read",
        "is_sent", "created_at"
    )
    fields = (
        "platform", "sender_type", "text", "attachment_url",
        "is_read", "is_sent", "created_at"
    )
    ordering = ("created_at",)


# =========================
# Conversation
# =========================
@admin.register(Conversation)
class ConversationAdmin(UnfoldModelAdmin):
    list_display = (
        "id", "platform", "social_account",
        "external_user_id", "external_username",
        "is_open", "last_message_at", "created_at"
    )
    list_filter = ("platform", "is_open", "social_account")
    search_fields = ("external_user_id", "external_username", "social_account__name")
    readonly_fields = ("created_at",)
    ordering = ("-last_message_at",)

    inlines = [MessageInline]

    fieldsets = (
        ("Basic Info", {
            "fields": ("social_account", "platform", "page_id", "profile_pic_url")
        }),
        ("User Info", {
            "fields": ("external_user_id", "external_username", "personal_info")
        }),
        ("Status", {
            "fields": ("is_open", "last_message_at", "created_at")
        }),
    )


# =========================
# Message
# =========================
@admin.register(Message)
class MessageAdmin(UnfoldModelAdmin):
    list_display = (
        "id", "conversation", "platform",
        "sender_type", "text", "is_read",
        "is_sent", "created_at"
    )
    list_filter = ("platform", "sender_type", "is_read", "is_sent")
    search_fields = ("text", "conversation__external_user_id", "conversation__social_account__name")
    readonly_fields = ("created_at",)
    ordering = ("created_at",)

    fieldsets = (
        ("Message Info", {
            "fields": ("conversation", "platform", "sender_type", "text", "attachment_url")
        }),
        ("Status", {
            "fields": ("is_read", "is_sent", "created_at")
        }),
    )
