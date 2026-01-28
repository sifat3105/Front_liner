import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()

from apps.assistant import routing as assistant_routing
from apps.call import routing as call_routing 
from apps.notification import routing as notification_routing
from apps.chat import routing as chat_routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(assistant_routing.websocket_urlpatterns + call_routing.websocket_urlpatterns + 
                notification_routing.websocket_urlpatterns + chat_routing.websocket_urlpatterns
            )
    ),
})