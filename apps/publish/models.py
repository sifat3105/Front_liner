from django.db import models
from django.contrib.auth import get_user_model
from apps.social.models import SocialPlatform
User = get_user_model()


class SocialPost(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="social_posts"
    )
    platforms = models.ManyToManyField(SocialPlatform, blank=True)

    title = models.CharField(max_length=255, blank=True)
    caption = models.TextField(help_text="Base caption/content")
    hashtags = models.JSONField(default=list, blank=True)

    scheduled_at = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=False)

    post_ids = models.JSONField(default=list, blank=True)
    error_message = models.TextField(blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Post {self.id} by {self.author}"
    

class PostMediaFile(models.Model):
    post = models.ForeignKey(SocialPost,on_delete=models.CASCADE,related_name="media")
    file = models.FileField(upload_to="social_posts/media/")
    media_type = models.CharField(max_length=10, default="image",
        choices=(("image", "Image"), ("video", "Video")))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.post.id} → {self.media_type}"

