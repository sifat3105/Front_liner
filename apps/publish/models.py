from django.db import models
from django.contrib.auth import get_user_model
from apps.social.models import SocialPlatform
User = get_user_model()

PLATFORM_CHOICES = (
    ('facebook', 'Facebook'),
    ('twitter', 'Twitter'),
    ('instagram', 'Instagram'),
    ('linkedin', 'LinkedIn'),
    ('tiktok', 'TikTok'),
    ('youtube', 'YouTube'),

)


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
    
    page_access_token = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Post {self.id} by {self.author}"
    
    @property
    def total_reactions(self):
        return self.reactions.count()

    @property
    def total_comments(self):
        return self.comments.count()
    

class PostMediaFile(models.Model):
    post = models.ForeignKey(SocialPost,on_delete=models.CASCADE,related_name="media")
    file = models.FileField(upload_to="social_posts/media/")
    media_type = models.CharField(max_length=10, default="image",
        choices=(("image", "Image"), ("video", "Video")))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.post.id} → {self.media_type}"
    
    
class MediaDraft(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to="social_posts/drafts/")
    media_type = models.CharField(max_length=10, default="image",
        choices=(("image", "Image"), ("video", "Video")))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.id} → {self.media_type}"
    
    

class Comment(models.Model):
    post = models.ForeignKey(SocialPost, on_delete=models.CASCADE, related_name="comments")
    
    text = models.TextField(blank=True)
    attachments = models.JSONField(default=list, blank=True)
    
    commenter_name = models.CharField(max_length=255, blank=True)
    commenter_id = models.CharField(max_length=255, blank=True)
    platform = models.CharField(max_length=255, blank=True, default="facebook",choices=PLATFORM_CHOICES)
    
    comment_id = models.CharField(max_length=255, blank=True)
    reactions_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
class SubComment(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="subcomments")
    
    text = models.TextField(blank=True)
    
    commenter_name = models.CharField(max_length=255, blank=True)
    commenter_id = models.CharField(max_length=255, blank=True)
    platform = models.CharField(max_length=255, blank=True, default="facebook",choices=PLATFORM_CHOICES)
    
    sub_comment_id = models.CharField(max_length=255, blank=True)
    reactions_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    

class Reaction(models.Model):
    post = models.ForeignKey(SocialPost, on_delete=models.CASCADE, related_name="reactions")
    
    reaction = models.CharField(max_length=255, blank=True)
    
    reactor_name = models.CharField(max_length=255, blank=True)
    reactor_id = models.CharField(max_length=255, blank=True)
    platform = models.CharField(max_length=255, blank=True, default="facebook",choices=PLATFORM_CHOICES)
    
    
