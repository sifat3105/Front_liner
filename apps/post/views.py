from utils.base_view import BaseAPIView as APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import CaptionGenerateSerializer
from .generate_post import generate_social_caption_from_image
from .models import GeneratedCaption


class GenerateCaptionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = CaptionGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        image_path = data.get("image_path")  # optional
        description = data.get("description", "")

        result = generate_social_caption_from_image(
            image_path=image_path,
            platform=data.get("platform", "instagram"),
            tone=data.get("tone", "friendly"),
            topic=data.get("topic", ""),
            call_to_action=data.get("call_to_action", "")
        )

        # Save to DB
        caption_obj = GeneratedCaption.objects.create(
            author=request.user,
            image_path=image_path,
            image_description=result.get("image_description", ""),
            description=description,
            platform=data.get("platform", "instagram"),
            tone=data.get("tone", "friendly"),
            topic=data.get("topic", ""),
            call_to_action=data.get("call_to_action", ""),
            captions=result.get("captions", []),
            selected_caption=result.get("selected_caption", ""),
            formatted_caption=result.get("formatted_caption", ""),
            hashtags=result.get("hashtags", []),
            character_count=result.get("character_count", 0),
            word_count=result.get("word_count", 0),
            within_limit=result.get("within_limit", False),
            max_length=result.get("max_length", 280),
        )

        response_data = {
            "id": caption_obj.id,  # return saved object id
            "captions": result.get("captions", []),
            "selected_caption": result.get("selected_caption", ""),
            "formatted_caption": result.get("formatted_caption", ""),
            "hashtags": result.get("hashtags", []),
            "character_count": result.get("character_count", 0),
            "word_count": result.get("word_count", 0),
            "within_limit": result.get("within_limit", False),
            "max_length": result.get("max_length", 280),
            "platform": result.get("platform", data.get("platform", "instagram")),
            "success": result.get("success", True), 
            "image_description": result.get("image_description", "")
        }

        return self.success(
            message="Caption generated successfully",
            status_code=status.HTTP_200_OK,
            data=response_data,
            meta={"action": "generate_caption"}
        )

