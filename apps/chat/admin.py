from django.contrib import admin
from django.utils.html import format_html, format_html_join, escape
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
        "text", "attachments_preview", "attachments", "is_read",
        "is_sent", "created_at"
    )
    fields = (
        "platform", "sender_type", "text", "attachments_preview", "attachments",
        "is_read", "is_sent", "created_at"
    )
    ordering = ("created_at",)

    def attachments_preview(self, obj: Message):
        return _render_attachments(obj.attachments)

    attachments_preview.short_description = "Attachments"


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
    readonly_fields = ("created_at", "chat_view")
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
            "fields": ("is_bot_active", "is_open", "last_message_at", "created_at")
        }),
        ("Chat", {
            "fields": ("chat_view",)
        }),
    )

    def chat_view(self, obj: Conversation):
        messages = obj.messages.all().order_by("created_at")
        if not messages:
            return "No messages yet."

        items = []
        for msg in messages:
            is_user = msg.sender_type == "customer"
            bubble_bg = "#f1f0f0" if is_user else "#dcf8c6"
            sender = escape(msg.sender_name or msg.sender_type.capitalize())
            time = msg.created_at.strftime("%Y-%m-%d %H:%M")
            text = escape(msg.text or "")

            avatar_url = msg.sender_profile_pic or obj.profile_pic_url or ""
            avatar_html = ""
            if is_user and avatar_url:
                avatar_html = format_html(
                    "<img src=\"{}\" style=\"width:28px;height:28px;border-radius:50%;object-fit:cover;\" />",
                    avatar_url
                )

            attachments_html = ""
            if msg.attachments:
                attachment_urls = []
                for att in msg.attachments or []:
                    payload = att.get("payload") or {}
                    url = payload.get("url") or att.get("url")
                    if url:
                        attachment_urls.append(url)
                if attachment_urls:
                    attachments_html = format_html_join(
                        "", "<div style='margin-top:6px;'><img src=\"{}\" style=\"max-width:220px;border-radius:10px;\" /></div>",
                        ((u,) for u in attachment_urls)
                    )

            if is_user:
                row = format_html(
                    "<div style='display:flex;align-items:flex-start;margin:10px 0;gap:10px;'>"
                    "<div style='width:28px;display:flex;justify-content:center;align-items:flex-start;'>{}</div>"
                    "<div style='max-width:70%;background:{};padding:10px 12px;border-radius:12px;"
                    "box-shadow:0 1px 2px rgba(0,0,0,.08);'>"
                    "<div style='font-size:11px;color:#666;margin-bottom:4px;'>{} · {}</div>"
                    "<div style='white-space:pre-wrap;font-size:13px;color:#111;'>{}</div>{}"
                    "</div>"
                    "</div>",
                    avatar_html, bubble_bg, sender, time, text, attachments_html
                )
            else:
                row = format_html(
                    "<div style='display:flex;justify-content:flex-end;margin:10px 0;'>"
                    "<div style='max-width:70%;background:{};padding:10px 12px;border-radius:12px;"
                    "box-shadow:0 1px 2px rgba(0,0,0,.08);'>"
                    "<div style='font-size:11px;color:#666;margin-bottom:4px;'>{} · {}</div>"
                    "<div style='white-space:pre-wrap;font-size:13px;color:#111;'>{}</div>{}"
                    "</div>"
                    "</div>",
                    bubble_bg, sender, time, text, attachments_html
                )

            items.append(row)

        return format_html(
            "<div style='background:#fff;border:1px solid #e5e5e5;border-radius:12px;padding:16px;"
            "max-height:70vh;overflow:auto;width:100%;max-width:100%;box-sizing:border-box;'>{}</div>",
            format_html_join("", "{}", ((item,) for item in items))
        )

    chat_view.short_description = "Chat"


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
    readonly_fields = ("created_at", "attachments_preview")
    ordering = ("-created_at",)

    fieldsets = (
        ("Message Info", {
            "fields": ("conversation", "platform", "sender_type", "text", "attachments_preview", "attachments")
        }),
        ("Status", {
            "fields": ("is_read", "is_sent", "created_at")
        }),
    )

    def attachments_preview(self, obj: Message):
        return _render_attachments(obj.attachments)

    attachments_preview.short_description = "Attachments"


def _render_attachments(attachments):
    attachment_urls = []
    for att in attachments or []:
        payload = att.get("payload") or {}
        url = payload.get("url") or att.get("url")
        if url:
            attachment_urls.append((url, att.get("type")))

    if not attachment_urls:
        return "—"

    previews = []
    for url, att_type in attachment_urls:
        is_image = att_type == "image" or url.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp"))
        if is_image:
            previews.append(
                format_html("<img src=\"{}\" style=\"max-width:140px;border-radius:8px;margin:4px 6px 0 0;\" />", url)
            )
        else:
            previews.append(format_html("<a href=\"{}\" target=\"_blank\">{}</a>", url, url))

    return format_html_join("", "{}", ((p,) for p in previews))
