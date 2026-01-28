from django.urls import path
from .views import (
    AgentsListCreateView, AgentDetailView,
    PublicVoiceStartView, PublicChatView,
    AgentEmbedInfoView, embed_js_v2, EmbedChatJsV1View
)

urlpatterns = [
    # Owner (dashboard)
    path("api/agents/", AgentsListCreateView.as_view()),
    path("api/agents/<int:pk>/", AgentDetailView.as_view()),
    path("api/agents/<int:pk>/embed/", AgentEmbedInfoView.as_view()),

    # Public embed (no-auth)
    path("api/embed/agents/<uuid:public_id>/voice/start/", PublicVoiceStartView.as_view()),
    path("api/embed/agents/<uuid:public_id>/chat/", PublicChatView.as_view()),
    path("embed/v2.js", embed_js_v2, name="voice-embed-js-v2"),
    path("embed/chat/v1.js", EmbedChatJsV1View.as_view(), name="embed-chat-js-v1"),

    # Assistant

]
