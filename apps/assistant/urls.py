from django.urls import path

from .views_history import AssistantHistoryListView, AssistantHistoryDetailView
from .views import (
    AssistantView, AssistantDetailView, TranscriptListView, TranscriptDetailView,
    AssistantLanguageAndVoiceView, AssistantEmbedView, VoicesListView, azure_preview,
    GenerateAssistantPromptView, AssistantSystemTraningView
    )
urlpatterns = [
    path('prompt/', GenerateAssistantPromptView.as_view(), name='assistant-prompt'),
    path('language-and-voice/', AssistantLanguageAndVoiceView.as_view(), name='assistant-language-and-voice'),
    path('', AssistantView.as_view(), name='assistant-list-create'),
    path('<int:assistant_id>/', AssistantDetailView.as_view(), name='assistant-detail'),
    path('embed', AssistantEmbedView.as_view(), name='assistant_embed'),
    path('system-training/', AssistantSystemTraningView.as_view(), name='assistant-system-training'),
    
    
    # Transcripts API Routes
    path("transcripts/", TranscriptListView.as_view(), name="transcript-list"),
    path("transcripts/<int:pk>/", TranscriptDetailView.as_view(), name="transcript-detail"),
    
    # Voice List API Routes
    path("voices/", VoicesListView.as_view(), name="elevenlabs-voices"),
    path("voices/<str:voice_id>/preview/", azure_preview, name="assistant-voice-preview"),
    
    # Assistant History API Routes
    path("<int:assistant_id>/history/", AssistantHistoryListView.as_view(), name="assistant-history-list"),
    path("<int:assistant_id>/history/<int:history_id>/", AssistantHistoryDetailView.as_view(), name="assistant-history-detail"),
    ]
