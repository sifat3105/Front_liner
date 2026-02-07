from rest_framework import serializers

class CaptionGenerateSerializer(serializers.Serializer):
    description = serializers.CharField(required=False, allow_blank=True)
    platform = serializers.ChoiceField(
        choices=["instagram", "facebook", "twitter", "linkedin", "tiktok"],
        required=False,
        default="instagram",
    )
    tone = serializers.CharField(required=False, default="friendly")
    topic = serializers.CharField(required=False, allow_blank=True)
    call_to_action = serializers.CharField(required=False, allow_blank=True)
    image_path = serializers.ImageField(required=False, allow_null=True)
