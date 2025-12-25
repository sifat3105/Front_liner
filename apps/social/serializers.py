from rest_framework import serializers
from .models import SocialAccount, FacebookPage

class SocialAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialAccount
        fields = (
            "id",
            "platform",
            "user_access_token",
            "fb_user_id",
            "ig_user_id",
            "tw_user_id",
            "yt_user_id",
            "li_user_id",
            "tk_user_id",
        )
        
class FacebookPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = FacebookPage
        fields = (
            "id",
            "page_name",
            "category",
            "category_list",
            "tasks",
            "is_active",
        )