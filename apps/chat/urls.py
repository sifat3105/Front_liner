from django.urls import path
from . import views

urlpatterns = [
    path('message/', views.ChatView.as_view()),
]