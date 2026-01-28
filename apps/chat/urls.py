from django.urls import path
from . import views

urlpatterns = [
    path("", views.ConversationListAPIView.as_view()),
    path("<int:conversation_id>/messages/", views.MessageAPIView.as_view()),
    path("<int:conversation_id>/mark-read/", views.MarkMessagesReadAPIView.as_view()),
]