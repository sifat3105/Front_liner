from django.urls import path
from .views import GenerateCaptionAPIView

urlpatterns = [
    path("generate-caption/", GenerateCaptionAPIView.as_view(), name="generate-caption"),
]
