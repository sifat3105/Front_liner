from rest_framework import serializers
from .models import CallLog

class CallLogSerializer(serializers.ModelSerializer):
    assistant_name = serializers.CharField(source='assistant.name', read_only=True)

    class Meta:
        model = CallLog
        fields = [
            "id",
            "assistant_name",
            "call_sid",
            "call_status",
            "call_duration",
            "caller",
            "callee",
            "timestamp",
            "recording_url",
            "record_sid",
            "created_at",
            "updated_at",
        ]
        
    