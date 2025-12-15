from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()


class SocialPlatform(models.TextChoices):
    FACEBOOK = "facebook", "Facebook"
    INSTAGRAM = "instagram", "Instagram"
    TIKTOK = "tiktok", "TikTok"
    X = "x", "X (Twitter)"
    LINKEDIN = "linkedin", "LinkedIn"

class SocialPost(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="social_posts"
    )

    title = models.CharField(max_length=255, blank=True)
    caption = models.TextField(help_text="Base caption/content")

    scheduled_at = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Post {self.id} by {self.author}"
    

class SocialMedia(models.Model):
    post = models.ForeignKey(
        SocialPost,
        on_delete=models.CASCADE,
        related_name="media"
    )

    file = models.FileField(upload_to="social_posts/media/")
    media_type = models.CharField(
        max_length=10,
        choices=(("image", "Image"), ("video", "Video"))
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.post.id} → {self.media_type}"



class SocialPostPublish(models.Model):
    post = models.ForeignKey(
        SocialPost,
        on_delete=models.CASCADE,
        related_name="publishes"
    )

    platform = models.CharField(
        max_length=20,
        choices=SocialPlatform.choices
    )

    platform_account_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Page ID, IG Business ID, LinkedIn Org ID, etc"
    )

    platform_post_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Returned by platform after publish"
    )

    custom_caption = models.TextField(
        blank=True,
        help_text="Override caption for this platform"
    )

    status = models.CharField(
        max_length=20,
        choices=(
            ("pending", "Pending"),
            ("scheduled", "Scheduled"),
            ("published", "Published"),
            ("failed", "Failed"),
        ),
        default="pending"
    )

    error_message = models.TextField(blank=True)

    published_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("post", "platform")

    def __str__(self):
        return f"{self.post.id} → {self.platform}"
