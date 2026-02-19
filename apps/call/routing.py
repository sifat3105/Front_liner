from django.urls import re_path
from .consumers import TwilioStreamConsumer, BridgeConsumer

websocket_urlpatterns = [
    re_path(r"^ws/twilio/stream/$", TwilioStreamConsumer.as_asgi()),
    re_path(r"^ws/agent$", BridgeConsumer.as_asgi()),
]