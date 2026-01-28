from django.urls import re_path
from .consumers import ChatConsumer, ChatBotConsumer

websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<conversation_id>\d+)/$", ChatConsumer.as_asgi(),),
    re_path(r"ws/chat/direct/$", ChatBotConsumer.as_asgi(),),
    re_path(r"ws/chat/direct/(?P<conversation_id>\d+)/$", ChatBotConsumer.as_asgi(),),
    re_path(r"ws/chat/bot/$", ChatBotConsumer.as_asgi(),),
    re_path(r"ws/chat/bot/(?P<conversation_id>\d+)/$", ChatBotConsumer.as_asgi(),),
]
