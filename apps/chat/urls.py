from django.urls import path
from . import views

urlpatterns = [
    path('message/', views.ChatView.as_view()),
    path('send/', views.Send_message.as_view()),
]