from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import NotificationSerializer
from .models import Notification
from django.contrib.auth import get_user_model

User = get_user_model()

class NotificationView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        limit = request.query_params.get("range", 7)
        try:
            limit = int(limit)
        except:
            limit = 7
        user = User.objects.prefetch_related("notifications").get(id=request.user.id)
        notifications = (
            user.notifications.all()
                .order_by("-created_at")[:limit]
                
        )
        serializer = NotificationSerializer(notifications, many=True)
        return Response({
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "Notifications fetched successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
        
    def post(self, request):
        try:
            user = User.objects.prefetch_related("notifications").get(id=request.user.id)
            notification_id = request.data.get("notification_id")
            if notification_id =="all":
                user.notifications.update(read=True)
            elif notification_id:
                notification = Notification.objects.get(id=notification_id)
                notification.read = True
                notification.save()
            else:
                return Response({
                    "status": "error",
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "Missing notification_id"
                }, status=status.HTTP_400_BAD_REQUEST)
        except Notification.DoesNotExist:
            return Response({
                "status": "error",
                "status_code": status.HTTP_404_NOT_FOUND,
                "message": "Notification not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "status": "error",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

