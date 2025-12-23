from rest_framework import serializers
from .models import SupportTicket, CallSupportTicket,Assistant

class SupportTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicket
        fields = "__all__"
        read_only_fields = ("created_by",)

    def create(self, validated_data):
        user = self.context["request"].user
        validated_data["created_by"] = user
        return super().create(validated_data)
    
class CallSupportTicketSerializer(serializers.ModelSerializer):
    public_id = serializers.CharField(write_only=True, required=False)
    class Meta:
        model = CallSupportTicket
        fields = "__all__"
        read_only_fields = ("created_by","update","status", "agent", "remarks")
        
    def create(self, validated_data):
        if 'public_id' not in validated_data:
            return super().create(validated_data)
        else:
            try:
                public_id = validated_data.pop('public_id')
                assistant = Assistant.objects.get(public_id=public_id)
                validated_data["agent"] = assistant
                return super().create(validated_data)
            except Assistant.DoesNotExist:
                return super().create(validated_data)
            
    
        
            
    
    
