import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "projects.settings")  # ✅ must come first
django.setup()  # ✅ initialize Django before importing your app code

from apps.assistant import routing  # import AFTER setup
from apps.call import routing as call_routing 
from apps.notification import routing as notification_routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(routing.websocket_urlpatterns + call_routing.websocket_urlpatterns + notification_routing.websocket_urlpatterns)
    ),
})