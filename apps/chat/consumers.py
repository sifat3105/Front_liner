import json
from urllib.parse import parse_qs

from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.social.models import SocialAccount
from apps.chat.whatsapp.service import send_whatsapp_text
from .chat_bot import chatbot_reply
from .models import Message, Conversation
from .utils import get_chat_history, get_page, send_message

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.room_group_name = f"chat_{self.conversation_id}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = (data.get("text") or data.get("message") or "").strip()
        attachments = data.get("attachments") or []

        msg = await self.save_message(message, attachments)
        if msg.text:
            await self.send_message_to_user(msg.text)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": msg.text,
                "sender_type": msg.sender_type,
                "attachments": msg.attachments,
                "created_at": str(msg.created_at),
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    @sync_to_async
    def save_message(self, text, attachments):
        conversation = Conversation.objects.get(id=self.conversation_id)
        return Message.objects.create(
            conversation=conversation,
            text=text,
            attachments=attachments or [],
            sender_type="seller",
            platform=conversation.platform,
            is_sent=True,
        )
        
    @sync_to_async
    def send_message_to_user(self, text):
        conversation = Conversation.objects.get(id=self.conversation_id)
        page_id = conversation.page_id
        recipient_id = conversation.external_user_id
        try:
            if conversation.platform == "whatsapp":
                wa_token = (
                    conversation.social_account.long_lived_token
                    or conversation.social_account.user_access_token
                )
                send_whatsapp_text(page_id, recipient_id, text, access_token=wa_token)
            else:
                page = get_page(page_id)
                send_message(page.page_access_token, recipient_id, text)

        except Exception as e:
            print(f"[send_message_to_user Error] {e}")
            
            
class ChatBotConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.query_params = parse_qs(self.scope.get("query_string", b"").decode())
        self.conversation_id = self.scope["url_route"]["kwargs"].get("conversation_id")
        if not self.conversation_id:
            self.conversation_id = self._get_query_param("conversation_id", "conv_id")
        self.conversation = None
        self.room_group_name = None
        self.is_new_conversation = False

        path = (self.scope.get("path") or "").lower()
        self.mode = "bot" if "/chat/bot" in path or "/chatbot" in path else "direct"
        self.bot_enabled = self._parse_bool(
            self._get_query_param("bot", "chatbot", "use_bot"),
            default=(self.mode == "bot"),
        )

        self.user = self.scope.get("user")
        self.owner_user_id = None
        self.external_user_id = None

        self.conversation = await self._resolve_conversation()
        if not self.conversation:
            await self.close(code=4404)
            return

        self.room_group_name = f"chat_{self.conversation.id}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        await self.send(text_data=json.dumps({
            "type": "conversation_init",
            "conversation_id": self.conversation.id,
            "bot_enabled": self.bot_enabled,
            "new_conversation": self.is_new_conversation,
        }))

    async def disconnect(self, close_code):
        if self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        if data.get("type") == "ping":
            await self.send(text_data=json.dumps({"type": "pong"}))
            return

        message = (data.get("text") or data.get("message") or "").strip()
        attachments = data.get("attachments") or []

        if not message and not attachments:
            return

        sender_type = data.get("sender_type") or self._default_sender_type()
        msg = await self._create_message(
            text=message,
            attachments=attachments,
            sender_type=sender_type,
            sender_name=data.get("sender_name"),
        )
        await self._broadcast_message(msg)

        if self.bot_enabled and sender_type != "bot":
            await self._handle_bot_reply(message, attachments)

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    def _get_query_param(self, *keys, default=None):
        for key in keys:
            values = self.query_params.get(key)
            if values:
                return values[0]
        return default

    def _parse_bool(self, value, default=False):
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}

    def _default_sender_type(self):
        if self._is_owner():
            return "admin"
        return "customer"

    def _is_owner(self):
        user = self.scope.get("user")
        if not (user and user.is_authenticated and self.conversation):
            return False
        try:
            return self.conversation.social_account.user_id == user.id
        except Exception:
            return False

    def _can_access(self, conversation):
        user = self.scope.get("user")
        if user and user.is_authenticated:
            if conversation.social_account_id and conversation.social_account.user_id == user.id:
                return True
            if str(conversation.external_user_id) == str(user.id):
                return True
        owner_id = self._get_query_param("owner_id", "seller_id")
        if owner_id and conversation.social_account_id and str(conversation.social_account.user_id) == str(owner_id):
            return True
        external_id = self._get_query_param("external_user_id", "peer_id", "visitor_id", "user_id")
        if external_id and str(conversation.external_user_id) == str(external_id):
            return True
        return False

    async def _resolve_conversation(self):
        if self.conversation_id:
            conversation = await self._get_conversation(self.conversation_id)
            if conversation:
                if not self._can_access(conversation):
                    return None
                self.owner_user_id = conversation.social_account.user_id
                self.external_user_id = conversation.external_user_id
                return conversation

        owner_user = await self._get_owner_user()
        if not owner_user:
            return None

        self.owner_user_id = owner_user.id
        self.external_user_id = self._get_external_user_id()
        external_username = self._get_query_param("external_username", "username")

        conversation, created = await self._get_or_create_conversation(
            owner_user=owner_user,
            external_user_id=self.external_user_id,
            external_username=external_username,
            bot_active=self.bot_enabled,
        )
        self.is_new_conversation = created
        return conversation

    def _get_external_user_id(self):
        external_id = self._get_query_param("external_user_id", "peer_id", "visitor_id", "user_id")
        if external_id:
            return str(external_id)
        if self.user and getattr(self.user, "is_authenticated", False):
            return str(self.user.id)
        session = self.scope.get("session")
        if session and session.session_key:
            return f"session:{session.session_key}"
        return f"anon:{self.channel_name}"

    async def _get_owner_user(self):
        if self.user and getattr(self.user, "is_authenticated", False):
            return self.user
        owner_id = self._get_query_param("owner_id", "seller_id")
        if not owner_id:
            return None
        return await self._get_user_by_id(owner_id)

    @database_sync_to_async
    def _get_user_by_id(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def _get_conversation(self, conversation_id):
        return Conversation.objects.select_related("social_account").filter(id=conversation_id).first()

    @database_sync_to_async
    def _get_or_create_conversation(
        self,
        owner_user,
        external_user_id,
        external_username=None,
        bot_active=False,
    ):
        social_account, _ = SocialAccount.objects.get_or_create(
            user=owner_user,
            platform="widget",
            defaults={
                "name": "Widget Chat",
                "user_access_token": "widget",
            },
        )
        conversation, created = Conversation.objects.get_or_create(
            social_account=social_account,
            platform="widget" if self.mode != "bot" else "widget_bot",
            external_user_id=str(external_user_id),
            defaults={
                "external_username": external_username or str(external_user_id),
                "personal_info": {},
                "is_bot_active": bot_active,
            },
        )
        self.conversation_id = conversation.id
        if bot_active and not conversation.is_bot_active:
            conversation.is_bot_active = True
            conversation.save(update_fields=["is_bot_active"])
        return conversation, created

    @database_sync_to_async
    def _create_message(
        self,
        text,
        attachments,
        sender_type,
        sender_name=None,
        sender_profile_pic=None,
        sender_metadata=None,
    ):
        msg = Message.objects.create(
            conversation_id=self.conversation.id or self.conversation_id,
            text=text or "",
            attachments=attachments or [],
            sender_type=sender_type,
            platform=self.conversation.platform,
            is_sent=True,
            sender_name=sender_name,
            sender_profile_pic=sender_profile_pic,
            sender_metadata=sender_metadata or {},
        )
        Conversation.objects.filter(id=self.conversation.id).update(last_message_at=timezone.now())
        return msg

    async def _broadcast_message(self, msg):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message_id": msg.id,
                "message": msg.text,
                "text": msg.text,
                "sender_type": msg.sender_type,
                "attachments": msg.attachments or [],
                "created_at": msg.created_at.isoformat(),
            },
        )

    async def _handle_bot_reply(self, user_text, attachments):
        history = await self._get_chat_history()
        bot_payload = await sync_to_async(chatbot_reply, thread_sensitive=False)(
            user_text or "",
            history,
            attachments or [],
            owner_user_id=self.owner_user_id,
            source_platform=getattr(self.conversation, "platform", None),
        )
        reply_text = (bot_payload or {}).get("reply") or ""
        if not reply_text:
            return
        bot_msg = await self._create_message(
            text=reply_text,
            attachments=[],
            sender_type="bot",
            sender_name="Bot",
        )
        await self._broadcast_message(bot_msg)

    @database_sync_to_async
    def _get_chat_history(self):
        conversation = Conversation.objects.get(id=self.conversation.id)
        return get_chat_history(conversation)
0.
