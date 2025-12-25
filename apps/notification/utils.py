import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification
from .serializers import NotificationSerializer

def send_realtime_notification(user_id, payload: dict):
    channel_layer = get_channel_layer()
    group_name = f"room_id_{user_id}"

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "notify_message",
            "payload": payload
        }
    )
    
def create_notification(user_id, title, message, read=False):
    
    notification = Notification.objects.create(
        user_id=user_id,
        title=title,
        message=message,
        read=read
    )
    data = NotificationSerializer(notification).data
    send_realtime_notification(user_id, data)
    return True