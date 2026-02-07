from rest_framework import serializers
from .models import SocialAccount, FacebookPage, SocialPlatform, WhatsAppBusinessAccount



class SocialPlatformSerializer(serializers.ModelSerializer):
    connect_url = serializers.SerializerMethodField()
    key = serializers.CharField(source='name')
    name = serializers.CharField(source='display_name')
    is_connected = serializers.SerializerMethodField()

    def get_is_connected(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        
        user = request.user
        if SocialAccount.objects.filter(
            user=user,
            platform=obj.name
        ).exists():
            return True
        if obj.name =="whatsapp" and WhatsAppBusinessAccount.objects.filter(
            user=user
            ).exists():
                return True
            
        return False
        

    class Meta:
        model = SocialPlatform
        fields = ['id','key', 'name', 'image', 'connect_url', 'is_connected']
    def get_connect_url(self, obj):
        request = self.context.get('request')
        base_url = request.build_absolute_uri('/')[:-1] if request else '' 
        return f"{base_url}/api/social/{obj.name}/connect/"

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


class WhatsAppBusinessAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhatsAppBusinessAccount
        fields = (
            "id",
            "business_id",
            "business_name",
            "waba_id",
            "waba_name",
            "phone_number_id",
            "display_phone_number",
            "created_at",
            "updated_at",
        )
