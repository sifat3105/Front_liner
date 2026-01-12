
from utils.base_view import BaseAPIView as APIView
from rest_framework import permissions
from . chat_bot import chatbot_reply
from .whatsapp.service import send_whatsapp_text

class ChatView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        return self.success(
            data={"message": "Hello World"}
        )
        
    def post(self, request):
        message = request.data.get("message")
        print(message)
        chat_history = request.data.get("chat_history", [])

        result = chatbot_reply(message, chat_history)
        return self.success(data=result)
    
    
class Send_message(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        PHONE_NUMBER_ID = 61586104842593
        TO_NUMBER = "8801790166212"          # Recipient in international format
        MESSAGE = "Hello from Front Liner!"
        res = send_whatsapp_text(PHONE_NUMBER_ID, TO_NUMBER, MESSAGE)
        print(res)
        return self.success(
            data={"message": "Hello World"}
        )
        