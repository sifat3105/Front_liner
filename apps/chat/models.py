from django.db import models
from apps.social.models import SocialAccount


class Platform:
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    WHATSAPP = "whatsapp"
    WIDGET = "widget"
    WIDGET_BOT = "widget_bot"

    CHOICES = [
        (FACEBOOK, "Facebook"),
        (INSTAGRAM, "Instagram"),
        (WHATSAPP, "WhatsApp"),
        (WIDGET, "Widget"),
        (WIDGET_BOT, "Widget Bot"),
    ]


class Conversation(models.Model):
    social_account = models.ForeignKey(
        SocialAccount,
        on_delete=models.CASCADE,
        related_name="conversations"
    )

    platform = models.CharField(max_length=20, choices=Platform.CHOICES)
    external_user_id = models.CharField(max_length=100)  # PSID / IG user id
    external_username = models.CharField(max_length=255, blank=True, null=True)
    page_id = models.CharField(max_length=100, blank=True, null=True)
    profile_pic_url = models.TextField(blank=True, null=True)
    personal_info = models.JSONField(default=dict, blank=True)  # meta profile data

    is_bot_active = models.BooleanField(default=True)
    is_open = models.BooleanField(default=True)
    last_message_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("platform", "social_account", "external_user_id")

    def __str__(self):
        return f"{self.platform} conversation {self.external_user_id}"


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages"
    )

    platform = models.CharField(max_length=20, choices=Platform.CHOICES)
    message_id = models.CharField(max_length=100, blank=True, null=True)

    sender_type = models.CharField(
        max_length=10,
        choices=[
            ("customer", "Customer"),
            ("admin", "Admin"),
            ("bot", "Bot"),
            ("seller", "Seller"),
            ("vendor", "Vendor"),
            ("system", "System"),
        ]
    )

    sender_name = models.CharField(max_length=255, blank=True, null=True)
    sender_profile_pic = models.TextField(blank=True, null=True)
    sender_metadata = models.JSONField(default=dict, blank=True)

    text = models.TextField(blank=True)
    attachments = models.JSONField(default=list, blank=True, null=True)

    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
    
