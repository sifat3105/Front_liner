from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class SocialPlatform(models.Model):
    name = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='social_platforms/', null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.display_name

class SocialAccount(models.Model):
    PLATFORM_CHOICES = (
        ('facebook', 'Facebook'),
        ('twitter', 'Twitter'),
        ('instagram', 'Instagram'),
        ('whatsapp', 'WhatsApp'),
        ('linkedin', 'LinkedIn'),
        ('tiktok', 'TikTok'),
        ('youtube', 'YouTube'),
        ('widget', 'Widget'),

    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="social_accounts")
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    name = models.CharField(max_length=255, null=True, blank=True)
    user_access_token = models.TextField()
    long_lived_token = models.TextField(null=True, blank=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)
    refresh_token = models.TextField(null=True, blank=True)
    refresh_expires_at = models.DateTimeField(null=True, blank=True)
    access_token_expires_at = models.DateTimeField(null=True, blank=True)
    access_token = models.TextField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    other_token = models.TextField(null=True, blank=True)
    other_expires_at = models.DateTimeField(null=True, blank=True)

    fb_user_id = models.CharField(max_length=255, null=True, blank=True)
    ig_user_id = models.CharField(max_length=255, null=True, blank=True)
    tw_user_id = models.CharField(max_length=255, null=True, blank=True)
    yt_user_id = models.CharField(max_length=255, null=True, blank=True)
    li_user_id = models.CharField(max_length=255, null=True, blank=True)
    tk_user_id = models.CharField(max_length=255, null=True, blank=True)


    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'platform')

    def __str__(self):
        return f"{self.user} - {self.platform}"
    

class FacebookPage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    social_account = models.ForeignKey(SocialAccount, on_delete=models.CASCADE, related_name='facebook_pages')

    page_id = models.CharField(max_length=255)
    page_name = models.CharField(max_length=255)
    category = models.CharField(max_length=255, null=True, blank=True)  
    category_list = models.JSONField(default=list, blank=True)
    page_access_token = models.TextField()
    tasks = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.page_name
    
    
class InstagramAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="instagram_accounts")
    social_account = models.ForeignKey(SocialAccount, on_delete=models.CASCADE, related_name="instagram_accounts")
    
    ig_user_id = models.CharField(max_length=255)
    username = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    profile_picture = models.TextField(null=True, blank=True)
    page_id = models.TextField()
    page_access_token = models.TextField()
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username
    
class WhatsAppBusinessAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    business_id = models.CharField(max_length=100)
    business_name = models.CharField(max_length=255)
    waba_id = models.CharField(max_length=100)
    waba_name = models.CharField(max_length=255)
    phone_number_id = models.CharField(max_length=100)
    display_phone_number = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "waba_id", "phone_number_id")
