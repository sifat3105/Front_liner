from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import SupportTicket
from .serializers import SupportTicketSerializer

class SupportTicketCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SupportTicketSerializer

    def post(self, request):
        serializer = SupportTicketSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": "success",
                "status_code": 201,
                "message": "Support ticket created successfully.",
                "data": serializer.data
            }, status=201)
        return Response({
            "status": "error",
            "status_code": 400,
            "message": "Support ticket creation failed.",
            "data": serializer.errors
        }, status=400)
        
        
class CallSupportTicketCreateView(APIView):
    permission_classes = []
    
    def post(self, request):
        serializer = SupportTicketSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": "success",
                "status_code": 201,
                "message": "Support ticket created successfully.",
                "data": serializer.data
            }, status=201)
        return Response({
            "status": "error",
            "status_code": 400,
            "message": "Support ticket creation failed.",
            "data": serializer.errors
        }, status=400)