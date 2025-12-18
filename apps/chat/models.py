from django.db import models
from apps.social.models import SocialAccount

class Platform:
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    WHATSAPP = "whatsapp"

    CHOICES = [
        (FACEBOOK, "Facebook"),
        (INSTAGRAM, "Instagram"),
        (WHATSAPP, "WhatsApp"),
    ]

class Conversation(models.Model):
    social_account = models.ForeignKey(
        SocialAccount,
        on_delete=models.CASCADE,
        related_name="conversations"
    )

    platform = models.CharField(max_length=20, choices=Platform.CHOICES)
    page_id = models.CharField(max_length=100, blank=True, null=True)
    profile_pic_url = models.URLField(blank=True, null=True)
    personal_info = models.JSONField(default=list, blank=True)

    external_user_id = models.CharField(max_length=100)  
    # Facebook sender_id / Instagram user id

    external_username = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

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
            ("page", "Page"),
            ("assistant", "Assistant"),
            ("marchant", "Marchant"),
            ("system", "System"),
        ]
    )

    text = models.TextField(blank=True)
    attachment_url = models.URLField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

