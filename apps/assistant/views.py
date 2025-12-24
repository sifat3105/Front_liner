from utils.base_view import BaseAPIView as APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, generics, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from django.http import StreamingHttpResponse
from apps.notification.utils import create_notification
from .models import  Assistant, Transcript
from .serializers import(
    AssistantSerializer, AssistantListSerializer, TranscriptSerializer, TranscriptListSerializer,
    AssistantWidgetSerializer
    )
from .agent_prompt_generator import generate_agentic_prompt
import asyncio
import requests
import os
from django.conf import settings

import azure.cognitiveservices.speech as speechsdk
AZURE_SPEECH_KEY = os.environ.get("AZURE_SPEECH_KEY")
AZURE_REGION = os.environ.get("AZURE_SPEECH_REGION")

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"



class AssistantLanguageAndVoiceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        language = [
            {"code": code, "name": name}
            for code, name in Assistant.LANGUAGES_CHOICES
        ]
        data = {
            "language": language,

        }

        return self.success(
            message="Language and Voice fetched successfully.",
            status_code=status.HTTP_200_OK,
            data=data,
            meta={"action": "assistant-language-and-voice"}
        )
    
    

    
class GenerateAssistantPromptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user_text = request.data.get("prompt")
            if not user_text:
                return self.error(
                    message="Missing 'prompt' parameter.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                    meta={"action": "assistant-prompt"}
                )

            # Run async prompt generation in event loop (blocking version)
            response = asyncio.run(generate_agentic_prompt(user_text))
            return self.success(
                message="Assistant prompt generated successfully.",
                data=response,
                status_code=status.HTTP_200_OK,
                meta={"action": "assistant-prompt"}
            )       


        except Exception as e:
            return Response({
                "status": "error",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "An unexpected error occurred during assistant prompt generation.",
                "data": {"detail": str(e)}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AssistantView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            obj = Assistant.objects.filter(owner=request.user)
            return self.success(
                message="Assistant fetched successfully.",
                data=AssistantListSerializer(obj, many=True).data,
                status_code=status.HTTP_200_OK,
                meta={"action": "assistant-list"}
            )
        except Assistant.DoesNotExist:
            return self.error(
                message="Assistant not found.",
                errors=None,
                status_code=status.HTTP_404_NOT_FOUND,
                meta={"action": "assistant-list"}
            )
    
    def post(self, request):
        try:
            serializer = AssistantSerializer(data=request.data, context={"request": request})
            if serializer.is_valid():
                owner = request.user
                name = serializer.validated_data.get("name")
                language = serializer.validated_data.get("language")
                voice = serializer.validated_data.get("voice")

                if Assistant.objects.filter(owner=owner, name=name, language=language, voice=voice).exists():
                    return self.error(
                        message="An assistant with the same name, language, and voice already exists.",
                        status_code=status.HTTP_400_BAD_REQUEST,
                        errors={"name": ["This name is already taken."]}
                        )

                serializer.save()
                # create_notification(
                #     user_id = request.user.id,
                #     title="Assistant Created",
                #     message=f"Your assistant '{name}' has been created successfully.",
                # )
                return self.success(
                    message="Assistant created successfully.",
                    data=AssistantSerializer(serializer.instance).data,
                    status_code=status.HTTP_201_CREATED,
                    meta={"action": "assistant-create"}
                )
            return self.error(
                message="Invalid data",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
                meta={"action": "assistant-create"}
            )               


        except Exception as e:
            return self.error(
                message="An unexpected error occurred during assistant creation.",
                errors={"detail": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "assistant-create"}
            )

class AssistantDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, assistant_id):
        try:
            obj = Assistant.objects.get(pk=assistant_id, owner=request.user)
            return self.success(
                message="Assistant fetched successfully.",
                data=AssistantSerializer(obj, context={"request": request}).data,
                status_code=status.HTTP_200_OK,
                meta={"action": "assistant-detail"}
            )
        except Assistant.DoesNotExist:
            return self.error(
                message="Assistant not found.",
                errors=None,
                status_code=status.HTTP_404_NOT_FOUND,
                meta={"action": "assistant-detail"}
            )
    
    def put(self, request, assistant_id):
        try:
            obj = Assistant.objects.get(pk=assistant_id, owner=request.user)
            serializer = AssistantSerializer(obj, data=request.data, partial=False, context={"request": request})
            if serializer.is_valid():
                serializer.save()
                return self.success(
                    message="Assistant updated successfully.",
                    data=AssistantSerializer(serializer.instance, context={"request": request}).data,
                    status_code=status.HTTP_200_OK,
                    meta={"action": "assistant-update"}
                )
            return self.error(
                message="Assistant update failed.",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
                meta={"action": "assistant-update"}
            )
        except Exception as e:
            return self.error(
                message="An unexpected error occurred during assistant update.",
                errors={"detail": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "assistant-update"}
            )

    def patch(self, request, assistant_id):

        try:
            obj = Assistant.objects.get(pk=assistant_id, owner=request.user)
            serializer = AssistantSerializer(obj, data=request.data, partial=True, context={"request": request})
            if serializer.is_valid():
                serializer.save()
                return self.success(
                    message="Assistant partially updated successfully.",
                    data=AssistantSerializer(serializer.instance, context={"request": request}).data,
                    status_code=status.HTTP_200_OK,
                    meta={"action": "assistant-partial-update"}
                )
            return self.error(
                message="Partial update failed.",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
                meta={"action": "assistant-partial-update"}
            )
        except Assistant.DoesNotExist:
            return self.error(
                message="Assistant not found.",
                errors=None,
                status_code=status.HTTP_404_NOT_FOUND,
                meta={"action": "assistant-detail"}
            )
        except Exception as e:
            return self.error(
                message="An unexpected error occurred during partial update.",
                errors={"detail": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "assistant-partial-update"}
            )
        

    def delete(self, request, assistant_id):
        try:
            obj = Assistant.objects.get(pk=assistant_id, owner=request.user)
            obj.delete()
            return self.success(
                message="Assistant deleted successfully.",
                status_code=status.HTTP_204_NO_CONTENT,
                meta={"action": "assistant-delete"}
            )
        except Exception as e:
            return self.error(
                message="An unexpected error occurred during assistant deletion.",
                errors={"detail": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "assistant-delete"}
            )
        

class AssistantEmbedView(APIView):
    def get(self, request):
        public_id = request.query_params.get("public_id")

        if not public_id:
            return Response({"error": "public_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            assistant = Assistant.objects.get(public_id=public_id)
        except Assistant.DoesNotExist:
            return Response({"error": "Assistant not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = AssistantWidgetSerializer(assistant)
        return Response(serializer.data)
        
#------------------------------------------------------------------------------
# Transcripts API Views
#------------------------------------------------------------------------------

class TranscriptPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "Transcripts fetched successfully.",
            "meta": {
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
            },
            "data": data
        })


class TranscriptListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TranscriptListSerializer
    pagination_class = TranscriptPagination

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["type", "ended_reason", "assistant"]
    search_fields = ["call_id", "assistant__name", ]
    ordering_fields = ["start_time", "end_time", "score"]
    ordering = ["-start_time"]

    def get_queryset(self):
        user = self.request.user
        return Transcript.objects.filter(assistant__owner=user).order_by("-start_time")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)

        return self.get_paginated_response(serializer.data)
    

class TranscriptDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TranscriptSerializer
    queryset = Transcript.objects.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        response = {
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "Transcript details fetched successfully.",
            "data": serializer.data,
        }
        return Response(response, status=status.HTTP_200_OK)
    
    
#-------------------------------------------------------------------------------
# List of Assistants voice 
#-------------------------------------------------------------------------------


def extract_voice_name(voice_id):

    # Split by '-'
    parts = voice_id.split('-')
    
    last_part = parts[-1]
    
    if last_part.endswith("Neural"):
        last_part = last_part[:-6]
    
    return last_part


import random

def get_sample_text_for_voice(voice_id=None):


    english_texts = [
        "Hello! I hope you are having a great day.",
        "This is a simple test sentence for my voice.",
        "The weather today is bright and sunny.",
        "I love reading books and learning new things.",
        "Testing text-to-speech with different voices is fun.",
        "Please enjoy listening to this short sample.",
        "Artificial voices are becoming more natural every day.",
        "Try speaking slowly and clearly to be understood.",
        "This is just a normal sentence for testing purposes.",
        "Feel free to experiment with any text you like."
    ]

    bangla_texts = [
        "হ্যালো! আশা করি আপনার দিনটি সুন্দর কাটছে।",
        "এটি আমার ভয়েসের জন্য একটি সাধারণ পরীক্ষা বাক্য।",
        "আজকের আবহাওয়া উজ্জ্বল এবং রৌদ্রোজ্জ্বল।",
        "আমি বই পড়তে এবং নতুন কিছু শিখতে ভালোবাসি।",
        "বিভিন্ন ভয়েস দিয়ে টেক্সট-টু-স্পিচ পরীক্ষা করা মজার।",
        "এই ছোট্ট নমুনা শুনে আনন্দ নিন।",
        "কৃত্রিম ভয়েস প্রতিদিন আরও প্রাকৃতিক হয়ে উঠছে।",
        "স্পষ্টভাবে এবং ধীরে ধীরে কথা বলুন যাতে বোঝা যায়।",
        "এটি পরীক্ষা করার জন্য একটি সাধারণ বাক্য।",
        "আপনি চাইলে যেকোনো বাক্য ব্যবহার করতে পারেন।"
    ]

    if voice_id and voice_id.lower().startswith("bn-"):
        return random.choice(bangla_texts)
    else:
        return random.choice(english_texts)


class VoicePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100
    
    def get_paginated_data(self, data):
        return {
            "items": data,
            "pagination": {
                "count": self.page.paginator.count,
                "page": self.page.number,
                "page_size": self.get_page_size(self.request),
                "next": self.get_next_link(),
                "previous": self.get_previous_link()
            }
        }


class VoicesListView(APIView):

    # pagination_class = VoicePagination

    def get(self, request):
        try:
            # ----------------------------
            # 1️⃣ Check session cache
            # ----------------------------
            session_key = "azure_voices"
            voices_data = request.session.get(session_key)

            if not voices_data:
                voices_data = self.fetch_azure_voices(request)
                request.session[session_key] = voices_data
                request.session.modified = True

            # ----------------------------
            # 2️⃣ Search filter
            # ----------------------------
            search = request.query_params.get("search")
            if search:
                search = search.lower()
                voices_data = [
                    v for v in voices_data
                    if search in (v["name"] or "").lower()
                    or search in (v["voice_id"] or "").lower()
                    or search in (v["language"] or "").lower()
                    or search in (v["locale"] or "").lower()
                    or search in (v["description"] or "").lower()
                ]

            return self.success(
                message="Azure voices fetched successfully",
                data=voices_data,
                status_code=status.HTTP_200_OK,
                meta={"action": "azure-voice-list"}
            )

        except Exception as e:
            return self.error(
                message="Failed to fetch Azure voices",
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "azure-voice-list"}
            )
    # ----------------------------
    # Azure voice fetch logic
    # ----------------------------
    def fetch_azure_voices(self, request):
        BASE_URL = request.build_absolute_uri()

        speech_config = speechsdk.SpeechConfig(
            subscription=AZURE_SPEECH_KEY,
            region=AZURE_REGION
        )

        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
        result = synthesizer.get_voices_async().get()

        if result.reason != speechsdk.ResultReason.VoicesListRetrieved:
            raise Exception("Failed to fetch Azure voices")

        formatted_data = []

        for v in result.voices:
            voice_id = getattr(v, "short_name", None)
            locale = getattr(v, "locale", None)

            formatted_data.append({
                "voice_id": voice_id,
                "name": extract_voice_name(voice_id),
                "language": locale,
                "locale": locale,
                "model_id": "azure-neural",
                "preview_url": f"{BASE_URL}{voice_id}/preview/",
                "description": getattr(v, "description", "Azure Neural Voice"),
                "category": v.voice_type.name if v.voice_type else None
            })

        return formatted_data




def azure_preview(request, voice_id):
    try:
        speech_config = speechsdk.SpeechConfig(
            subscription=AZURE_SPEECH_KEY,
            region=AZURE_REGION
        )
        speech_config.speech_synthesis_voice_name = voice_id
        speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
        )

        # Create a pull stream to read audio as it is generated
        stream = speechsdk.audio.PullAudioOutputStream()
        audio_config = speechsdk.audio.AudioOutputConfig(stream=stream)

        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=None  # We'll use the pull stream
        )

        text = get_sample_text_for_voice(voice_id)

        # Start synthesis asynchronously
        result_future = synthesizer.speak_text_async(text)

        # Generator function to yield audio chunks
        def audio_generator():
            result = result_future.get()
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                # Yield bytes in chunks
                chunk_size = 1024
                audio_data = result.audio_data
                for i in range(0, len(audio_data), chunk_size):
                    yield audio_data[i:i + chunk_size]

        response = StreamingHttpResponse(
            audio_generator(),
            content_type="audio/mpeg"
        )
        response["Content-Disposition"] = f'inline; filename="{voice_id}_sample.mp3"'
        return response

    except Exception as e:
        return StreamingHttpResponse(f"Error: {str(e)}", status=500)