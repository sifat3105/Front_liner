from rest_framework import serializers
from .models import SocialPost, PostMediaFile

class SocialMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostMediaFile
        fields = ("id", "file", "media_type", "created_at", "updated_at")
        
        
class SocialPostCreateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, allow_blank=True)
    caption = serializers.CharField()
    hashtags = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    scheduled_at = serializers.DateTimeField(required=False, allow_null=True)
    is_published = serializers.BooleanField(default=False)
    platforms = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )


class SocialPostSerializer(serializers.ModelSerializer):
    media = SocialMediaSerializer(many=True, required=False)
    platforms = serializers.SerializerMethodField()
    
    class Meta:
        model = SocialPost
        fields = (
            "id", "title", "caption", "scheduled_at", 
            "is_published", "media", "platforms", "post_ids", "created_at", "updated_at"
        )
        
    def get_platforms(self, obj):
        return [{"id": p.id, "platform": p.name} for p in obj.platforms.all()]
    
    def create(self, validated_data):
        # Get media data if provided
        media_data = validated_data.pop('media', [])
        
        # Create the post first
        post = SocialPost.objects.create(
            author=self.context['request'].user,
            **validated_data
        )
        
        # Create associated media objects
        for media_item in media_data:
            PostMediaFile.objects.create(post=post, **media_item)
        
        return post
    
    def update(self, instance, validated_data):
        media_data = validated_data.pop('media', None)
        
        # Update post fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # If media data is provided, update media (clear and recreate)
        if media_data is not None:
            # Delete existing media
            instance.media.all().delete()
            
            # Create new media
            for media_item in media_data:
                PostMediaFile.objects.create(post=instance, **media_item)
        
        return instance
    
    def update(self, instance, validated_data):
        media = validated_data.pop("media")
        instance.title = validated_data.get("title", instance.title)
        instance.caption = validated_data.get("caption", instance.caption)
        instance.scheduled_at = validated_data.get("scheduled_at", instance.scheduled_at)
        instance.is_published = validated_data.get("is_published", instance.is_published)
        instance.save()
        if media:
            for m in media:
                PostMediaFile.objects.create(post=instance, **m)
        return instance


    