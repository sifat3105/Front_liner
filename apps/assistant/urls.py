from django.urls import path
from .views import (
    AssistantView, AssistantDetailView, TranscriptListView, TranscriptDetailView,
    AssistantLanguageAndVoiceView, AssistantEmbedView, VoicesListView, azure_preview,
    GenerateAssistantPromptView
    )
urlpatterns = [
    path('assistants/prompt/', GenerateAssistantPromptView.as_view(), name='assistant-prompt'),
    path('assistants/language-and-voice/', AssistantLanguageAndVoiceView.as_view(), name='assistant-language-and-voice'),
    path('assistants/', AssistantView.as_view(), name='assistant-list-create'),
    path('assistants/<int:assistant_id>/', AssistantDetailView.as_view(), name='assistant-detail'),
    path('embed/', AssistantEmbedView.as_view(), name='assistant_embed'),
    
    # Transcripts API Routes
    path("transcripts/", TranscriptListView.as_view(), name="transcript-list"),
    path("transcripts/<int:pk>/", TranscriptDetailView.as_view(), name="transcript-detail"),
    
    # Voice List API Routes
    path("voices/", VoicesListView.as_view(), name="elevenlabs-voices"),
    path("voices/<str:voice_id>/preview/", azure_preview, name="elevenlabs-voice-preview"),

    ]
