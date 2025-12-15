from rest_framework import serializers

class CaptionGenerateSerializer(serializers.Serializer):
    description = serializers.CharField()
    platform = serializers.ChoiceField(choices=["instagram", "facebook", "twitter", "linkedin"])
    tone = serializers.CharField(required=False, allow_blank=True)
    topic = serializers.CharField(required=False, allow_blank=True)
    call_to_action = serializers.CharField(required=False, allow_blank=True)
    image_description = serializers.CharField(required=False, allow_blank=True)
