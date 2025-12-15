from utils.base_view import BaseAPIView as APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import CaptionGenerateSerializer
from .generate_post import generate_social_caption  


class GenerateCaptionAPIView(APIView):
    
    def post(self, request):
        serializer = CaptionGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        result = generate_social_caption(
            description=data["description"],
            platform=data["platform"],
            tone=data.get("tone"),
            topic=data.get("topic"),
            call_to_action=data.get("call_to_action"),
            image_description=data.get("image_description"),
        )

        return Response({
            "captions": result["captions"],
            "selected_caption": result["selected_caption"],
            "hashtags": result["hashtags"],
            "character_count": result["character_count"],
            "max_length": result["max_length"],
            "within_limit": result["within_limit"],
        }, status=status.HTTP_200_OK)
