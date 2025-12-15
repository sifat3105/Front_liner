from django.urls import path
from .views import CustomerInfoAPIView

urlpatterns = [
    path('sells/', CustomerInfoAPIView.as_view(), name='sells-list'),
]
