
from utils.base_view import BaseAPIView as APIView
from rest_framework import permissions
from . chat_bot import chatbot_reply

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
        