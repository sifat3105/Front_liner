from rest_framework import serializers
from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "text", "sender_type", "attachments", "is_read", "created_at",]
        

            


class ConversationSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    ws_url = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ["id", "platform", "profile_pic_url", "personal_info", "external_username", "last_message", "ws_url"]

    def get_last_message(self, obj):
        msg = obj.messages.last()
        return MessageSerializer(msg, context=self.context).data if msg else None

    def get_ws_url(self, obj):
        request = self.context.get("request")
        if not request:
            return ""
        scheme = "wss" if request.is_secure() else "ws"
        host = request.get_host()
        platform = (getattr(obj, "platform", "") or "").lower()
        if platform == "widget" or platform == "direct":
            path = f"/ws/chat/direct/{obj.id}/"
        elif platform == "widget_bot":
            path = f"/ws/chat/bot/{obj.id}/"
        else:
            path = f"/ws/chat/{obj.id}/"
        return f"{scheme}://{host}{path}"
