from rest_framework.permissions import IsAuthenticated
from utils.base_view import BaseAPIView as APIView
from .models import Assistant, AssistantHistory
from .serializers import AssistantHistoryListSerializer, AssistantHistoryDetailSerializer
from rest_framework import status


class AssistantHistoryListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, assistant_id):
        try:
            assistant = Assistant.objects.get(
                id=assistant_id,
                owner=request.user
            )
        except Assistant.DoesNotExist:
            return self.error(
                message="Assistant not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        history = AssistantHistory.objects.filter(
            assistant=assistant
        ).order_by("-created_at")

        serializer = AssistantHistoryListSerializer(history, many=True)
        return self.success(
            message="Assistant history list fetched successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
            meta={"action": "assistant-history-list"}
        )
        
        
class AssistantHistoryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, assistant_id, history_id):
        try:
            assistant = Assistant.objects.get(
                id=assistant_id,
                owner=request.user
            )
            history = AssistantHistory.objects.get(
                id=history_id,
                assistant=assistant
            )
        except (Assistant.DoesNotExist, AssistantHistory.DoesNotExist):
            return self.error(
                message="History not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = AssistantHistoryDetailSerializer(history)
        return self.success(
            message="Assistant history detail fetched successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
            meta={"action": "assistant-history-detail"}
        )

