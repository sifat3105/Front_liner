import requests
from django.utils import timezone
from apps.social.models import FacebookPage
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Conversation, Message
from .chat_bot import chatbot_reply


FACEBOOK_API_URL = "https://graph.facebook.com/v19.0/me/messages"
REQUEST_TIMEOUT = 5


# ------------------ Facebook API ------------------ #

def send_message(page_access_token: str, recipient_id: str, text: str) -> dict:
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text},
    }
    params = {"access_token": page_access_token}

    try:
        response = requests.post(
            FACEBOOK_API_URL,
            json=payload,
            params=params,
            timeout=REQUEST_TIMEOUT
        )

        if response.status_code >= 400:
            try:
                err = (response.json() or {}).get("error", {})
            except ValueError:
                err = {}
            print(
                "[Facebook API Error] send_message failed "
                f"status={response.status_code} code={err.get('code')} "
                f"subcode={err.get('error_subcode')} message={err.get('message')}"
            )
            return {}

        return response.json()
    except requests.RequestException as e:
        print(f"[Facebook API Error] send_message request failed: {e}")
        return {}


# ------------------ Facebook API (async) ------------------ #

def get_fb_user_profile(psid: str, page_access_token: str) -> dict:
    url = f"https://graph.facebook.com/v19.0/{psid}"
    params = {
        "fields": "first_name,last_name,profile_pic",
        "access_token": page_access_token
    }
    try:
        r = requests.get(url, params=params, timeout=10)
    except requests.RequestException as e:
        raise RuntimeError(
            f"Profile request failed for psid={psid}: {e}"
        ) from e

    if r.status_code >= 400:
        try:
            err = (r.json() or {}).get("error", {})
        except ValueError:
            err = {}
        raise RuntimeError(
            "Profile request failed for "
            f"psid={psid} status={r.status_code} code={err.get('code')} "
            f"subcode={err.get('error_subcode')} message={err.get('message')}"
        )

    try:
        return r.json()
    except ValueError as e:
        raise RuntimeError(
            f"Profile request failed for psid={psid}: non-JSON response"
        ) from e



# ------------------ Database Helpers ------------------ #

from asgiref.sync import sync_to_async

@sync_to_async
def get_page_sync(page_id):
    return FacebookPage.objects.get(page_id=page_id)

def get_page(page_id: str) -> FacebookPage:
    return FacebookPage.objects.select_related("social_account").get(
        page_id=page_id
    )


def get_or_create_conversation(external_user_id: str, page: FacebookPage, user_data):
    print("get_or_create_conversation")
    conversation = None
    try:
        conversation, _ = Conversation.objects.get_or_create(
            external_user_id=external_user_id,
            social_account=page.social_account,
            page_id=page.page_id,
            defaults={
                "platform": page.social_account.platform,
                "external_username": (user_data.get("first_name", "") + " " + user_data.get("last_name", "")).strip(),
                "profile_pic_url": user_data.get("profile_pic"),
                "personal_info": user_data or {},
            },
        )
    except Exception as e:
        print(f"[DB Error] {e}")
    return conversation


def get_chat_history(conversation: Conversation) -> list:
    
    ROLE_MAP = {
        "customer": "user",
        "bot": "assistant",
        "seller": "user",
    }
    history = []

    for msg in conversation.messages.all().order_by("created_at"):
        role = ROLE_MAP.get(msg.sender_type, "user")
        content = msg.text
        if msg.sender_type == "seller":
            content = f"Seller: {content}"

        history.append({
            "role": role,
            "content": content,
            "time": msg.created_at.isoformat(),
        })

    return history


def store_chat_message(
    conversation: Conversation,
    sender_type: str,
    text: str = None,
    attachments: list = None,
    message_id: str = None,
    is_sent: bool = True,
    is_read: bool = False,
    sender_name: str = None,
    sender_profile_pic: str = None,
    sender_metadata: dict = None,
) -> None:
    try:
        message = Message.objects.create(
        conversation=conversation,
        sender_type=sender_type,
        platform=conversation.platform,
        message_id=message_id,
        is_sent=is_sent,
        is_read=is_read,
        )
        message.text = text or ""
        message.attachments = attachments or []
        message.sender_name = sender_name
        message.sender_profile_pic = sender_profile_pic
        message.sender_metadata = sender_metadata or {}
        message.save()
        conversation.last_message_at = timezone.now()
        conversation.save(update_fields=["last_message_at"])
        send_to_socket(conversation, message)
    except Exception as e:
        print(f"[DB Error] {e}")


# ------------------ Message Handler ------------------ #

def handle_message(
    page_id: str,
    sender_id: str,
    text: str,
    attachments: list = None,
    message_id: str = None,
) -> None:
    print("handle_message")
    page = get_page(page_id)

    if message_id:
        existing = Message.objects.filter(
            conversation__external_user_id=sender_id,
            conversation__social_account=page.social_account,
            message_id=message_id,
            sender_type="customer",
        ).exists()
        if existing:
            return
    user_data = {}
    try:
        user_data = get_fb_user_profile(sender_id, page.page_access_token)
    except Exception as e:
        print(
            f"[FB][ERROR] get_fb_user_profile: page_id={page_id} "
            f"sender_id={sender_id} error={e}"
        )
    conversation = get_or_create_conversation(
        external_user_id=sender_id,
        page=page,
        user_data=user_data
    )
    if not conversation:
        return
    sender_name = (user_data.get("first_name", "") + " " + user_data.get("last_name", "")).strip()
    
    raw_text = (text or "").strip()
    store_chat_message(
        conversation,
        "customer",
        raw_text,
        attachments,
        message_id=message_id,
        sender_name=sender_name,
        sender_profile_pic=user_data.get("profile_pic"),
        sender_metadata=user_data,
    )

    if _has_sticker(attachments):
        return

    history = get_chat_history(conversation)
    bot_response = chatbot_reply(
        raw_text,
        history,
        attachments or [],
        owner_user_id=page.user_id,
        source_platform=conversation.platform,
    )

    reply_text = bot_response.get("reply", "")
    if not reply_text:
        return

    send_resp = send_message(page.page_access_token, sender_id, reply_text)
    store_chat_message(
        conversation,
        "bot",
        reply_text,
        message_id=send_resp.get("message_id"),
        is_sent=bool(send_resp),
        sender_name="Bot",
    )


def _has_sticker(attachments: list) -> bool:
    for attachment in attachments or []:
        payload = attachment.get("payload") or {}
        if payload.get("sticker_id") or attachment.get("sticker_id"):
            return True
    return False


def get_conversation_for_user(page_id: str, external_user_id: str):
    page = get_page(page_id)
    return Conversation.objects.filter(
        external_user_id=external_user_id,
        social_account=page.social_account,
    ).first()


def mark_messages_delivered(page_id: str, external_user_id: str, mids: list):
    if not mids:
        return
    conversation = get_conversation_for_user(page_id, external_user_id)
    if not conversation:
        return
    Message.objects.filter(
        conversation=conversation,
        message_id__in=mids,
    ).update(is_sent=True)


def mark_messages_read(page_id: str, external_user_id: str, watermark_ms: int):
    conversation = get_conversation_for_user(page_id, external_user_id)
    if not conversation or not watermark_ms:
        return
    watermark_dt = timezone.datetime.fromtimestamp(
        watermark_ms / 1000, tz=timezone.get_current_timezone()
    )
    Message.objects.filter(
        conversation=conversation,
        sender_type="bot",
        created_at__lte=watermark_dt,
    ).update(is_read=True)
    
    
def send_to_socket(conversation, message):
    
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    async_to_sync(channel_layer.group_send)(
        f"chat_{conversation.id}",
        {
            "type": "chat_message",
            "message_id": message.id,
            "text": message.text,
            "sender_type": message.sender_type,
            "created_at": message.created_at.isoformat(),
        }
    )
