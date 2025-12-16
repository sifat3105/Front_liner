from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class GeneratedCaption(models.Model):
    PLATFORM_CHOICES = [
        ("instagram", "Instagram"),
        ("facebook", "Facebook"),
        ("twitter", "Twitter"),
        ("linkedin", "LinkedIn"),
        # add more platforms if needed
    ]

    TONE_CHOICES = [
        ("friendly", "Friendly"),
        ("formal", "Formal"),
        ("funny", "Funny"),
        ("serious", "Serious"),
        # add more tones if needed
    ]

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="captions")
    image_path = models.CharField(max_length=500, blank=True, null=True)
    image_description = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES, default="instagram")
    tone = models.CharField(max_length=50, choices=TONE_CHOICES, default="friendly")
    topic = models.CharField(max_length=255, blank=True, null=True)
    call_to_action = models.CharField(max_length=255, blank=True, null=True)

    captions = models.JSONField(default=list, blank=True)  # list of generated captions
    selected_caption = models.TextField(blank=True, null=True)
    formatted_caption = models.TextField(blank=True, null=True)
    hashtags = models.JSONField(default=list, blank=True)  # list of hashtags
    character_count = models.PositiveIntegerField(default=0)
    word_count = models.PositiveIntegerField(default=0)
    within_limit = models.BooleanField(default=True)
    max_length = models.PositiveIntegerField(default=280)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.platform} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
