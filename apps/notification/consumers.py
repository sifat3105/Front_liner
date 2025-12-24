from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from concurrent.futures import ThreadPoolExecutor
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
import json

User = get_user_model() 
@database_sync_to_async
def get_user(user_id):
    return User.objects.prefetch_related("notifications").get(id=user_id)

@database_sync_to_async
def make_notifications_read(user, notification_id):
    if notification_id == "all":
        user.notifications.update(read=True)
    else:
        notification = user.notifications.get(id=notification_id)
        notification.read = True
        notification.save()

class NotificationConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.executor = ThreadPoolExecutor(max_workers=1)
    async def connect(self):
        self.room_group_name = f"room_id_{self.scope['url_route']['kwargs']['user_id']}"
        user = await get_user(self.scope["url_route"]["kwargs"]["user_id"])
        self.scope["user"] = user
        await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
        await self.accept()
    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
    async def notify_message(self, event):
        payload = event["payload"]
        await self.send(text_data=json.dumps(payload))
    
    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        read = data.get("read", False)
        if read:
            await make_notifications_read(self.scope["user"], data.get("notification_id"))
        
        