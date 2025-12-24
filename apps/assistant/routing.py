from django.urls import re_path
from .consumers import AssistantConsumer

websocket_urlpatterns = [
    re_path(r"ws/assistant/(?P<session_id>[^/]+)/(?P<public_id>[^/]+)/$", AssistantConsumer.as_asgi()),
]
