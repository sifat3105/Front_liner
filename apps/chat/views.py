
from utils.base_view import BaseAPIView as APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer



class ConversationListAPIView(APIView):
    def get(self, request):
        conversations = Conversation.objects.filter(
            social_account__user=request.user
        ).order_by("-last_message_at")

        serializer = ConversationSerializer(conversations, many=True, context={"request": request})
        return self.success(data=serializer.data, message="Conversations retrieved successfully")


class MessageAPIView(APIView):

    def get(self, request, conversation_id):
        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            social_account__user=request.user
        )

        messages = Message.objects.filter(conversation=conversation).order_by("-created_at")
        serializer = MessageSerializer(messages, many=True, context={"request": request})
        return self.success(data=serializer.data, message="Messages retrieved successfully")
    
class MarkMessagesReadAPIView(APIView):
    def post(self, request, conversation_id):
        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            social_account__user=request.user
        )

        Message.objects.filter(
            conversation=conversation,
            sender_type="customer",
            is_read=False
        ).update(is_read=True)

        return self.success(message="Messages marked as read successfully")
    



