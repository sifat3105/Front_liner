import logging
import json

from django.conf import settings
from django.utils import timezone
from apps.chat.chat_bot import chatbot_reply
from apps.chat.models import Conversation, Message
from apps.chat.utils import (
    handle_message,
    mark_messages_delivered,
    mark_messages_read,
    send_to_socket,
)
from apps.chat.whatsapp.service import send_whatsapp_text
from apps.publish.services.post_dispatch_feed import (
    create_comment,
    create_comment_reply,
    update_comment,
    update_comment_reply,
    delete_comment,
    delete_comment_reply,
    create_reaction,
    update_reaction,
    delete_reaction,
    sync_post_from_facebook,
    delete_post_from_feed,
    save_post_media_from_link,
)
from apps.social.models import SocialAccount, WhatsAppBusinessAccount

logger = logging.getLogger(__name__)


# -------------------------
# Helpers
# -------------------------
def normalize_verb(raw_verb):

    v = (raw_verb or "").lower().strip()

    if v in ("add", "added", "create", "created"):
        return "add"
    if v in ("edit", "edited", "update", "updated"):
        return "update"
    if v in ("remove", "removed", "delete", "deleted"):
        return "delete"

    return "unknown"


def safe_lower(x):
    return (x or "").lower().strip()


def extract_attachments(value: dict):
    attachments = value.get("attachments")
    if attachments is None:
        attachment = value.get("attachment")
        if attachment:
            if isinstance(attachment, list):
                attachments = attachment
            else:
                attachments = [attachment]
        else:
            attachments = []
    return attachments or []


def _is_comment_reply(value: dict) -> bool:
    parent_id = value.get("parent_id")
    post_id = value.get("post_id")
    return bool(parent_id and post_id and parent_id != post_id)


# -------------------------
# FEED handlers (Page feed)
# -------------------------

def handle_comment_add(page_id: str, value: dict):
    post_id = value.get("post_id")
    comment_id = value.get("comment_id")
    text = value.get("message", "")
    user = value.get("from", {}) or {}
    user_name = user.get("name")
    user_id = user.get("id")
    attachments = extract_attachments(value)
    parent_id = value.get("parent_id")

    if _is_comment_reply(value):
        create_comment_reply(
            post_id=post_id,
            parent_comment_id=parent_id,
            sub_comment_id=comment_id,
            text=text,
            commenter_id=user_id,
            commenter_name=user_name,
            page_id=page_id,
        )
        logger.info(
            f"[FEED][COMMENT_REPLY][ADD] page={page_id} post={post_id} "
            f"parent={parent_id} sub_comment={comment_id} by={user_name}({user_id})"
        )
        return

    create_comment(
        post_id,
        comment_id,
        text,
        user_id,
        user_name,
        attachments=attachments,
        page_id=page_id,
    )

    logger.info(
        f"[FEED][COMMENT][ADD] page={page_id} post={post_id} comment={comment_id} "
        f"by={user_name}({user_id}) text={text} attachments={len(attachments)}"
    )


def handle_comment_update(page_id: str, value: dict):
    post_id = value.get("post_id")
    comment_id = value.get("comment_id")
    text = value.get("message", "")
    user = value.get("from", {}) or {}
    user_name = user.get("name")
    user_id = user.get("id")
    attachments = extract_attachments(value)
    parent_id = value.get("parent_id")

    if _is_comment_reply(value):
        update_comment_reply(
            post_id=post_id,
            parent_comment_id=parent_id,
            sub_comment_id=comment_id,
            text=text,
            commenter_id=user_id,
            commenter_name=user_name,
            page_id=page_id,
        )
        logger.info(
            f"[FEED][COMMENT_REPLY][UPDATE] page={page_id} post={post_id} "
            f"parent={parent_id} sub_comment={comment_id} by={user_name}({user_id})"
        )
        return

    update_comment(
        post_id,
        comment_id,
        text=text,
        commenter_id=user_id,
        commenter_name=user_name,
        attachments=attachments,
        page_id=page_id,
    )

    logger.info(
        f"[FEED][COMMENT][UPDATE] page={page_id} post={post_id} comment={comment_id} "
        f"by={user_name}({user_id}) text={text} attachments={len(attachments)}"
    )


def handle_comment_delete(page_id: str, value: dict):
    post_id = value.get("post_id")
    comment_id = value.get("comment_id")
    user = value.get("from", {}) or {}
    user_name = user.get("name")
    user_id = user.get("id")
    parent_id = value.get("parent_id")

    if _is_comment_reply(value):
        delete_comment_reply(post_id, parent_id, comment_id, page_id=page_id)
        logger.info(
            f"[FEED][COMMENT_REPLY][DELETE] page={page_id} post={post_id} "
            f"parent={parent_id} sub_comment={comment_id} by={user_name}({user_id})"
        )
        return

    delete_comment(post_id, comment_id, page_id=page_id)

    logger.info(
        f"[FEED][COMMENT][DELETE] page={page_id} post={post_id} comment={comment_id} "
        f"by={user_name}({user_id})"
    )


def handle_reaction_add(page_id: str, value: dict):
    post_id = value.get("post_id")
    reaction_type = value.get("reaction_type")
    user = value.get("from", {}) or {}
    user_name = user.get("name")
    user_id = user.get("id")

    create_reaction(post_id, reaction_type, user_id, user_name, page_id=page_id)

    logger.info(
        f"[FEED][REACTION][ADD] page={page_id} post={post_id} reaction={reaction_type} "
        f"by={user_name}({user_id})"
    )
    
def handle_reaction_update(page_id: str, value: dict):
    post_id = value.get("post_id")
    reaction_type = value.get("reaction_type")
    user = value.get("from", {}) or {}
    user_name = user.get("name")
    user_id = user.get("id")
    
    update_reaction(post_id, reaction_type, user_id, page_id=page_id)
    
    logger.info(
        f"[FEED][REACTION][UPDATE] page={page_id} post={post_id} reaction={reaction_type} "
        f"by={user_name}({user_id})"
    )


def handle_reaction_delete(page_id: str, value: dict):
    post_id = value.get("post_id")
    reaction_type = value.get("reaction_type")
    user = value.get("from", {}) or {}
    user_name = user.get("name")
    user_id = user.get("id")

    delete_reaction(post_id, reaction_type, user_id, page_id=page_id)

    logger.info(
        f"[FEED][REACTION][DELETE] page={page_id} post={post_id} reaction={reaction_type} "
        f"by={user_name}({user_id})"
    )


def handle_status_add(page_id: str, value: dict):
    post_id = value.get("post_id")
    text = value.get("message", "")
    user = value.get("from", {}) or {}
    user_name = user.get("name")
    user_id = user.get("id")
    link = value.get("link")
    item = safe_lower(value.get("item"))

    post = sync_post_from_facebook(post_id, page_id)
    if link and post:
        media_type = "video" if item == "video" else "image"
        save_post_media_from_link(post, link, media_type=media_type)

    logger.info(
        f"[FEED][STATUS][ADD] page={page_id} post={post_id} by={user_name}({user_id}) text={text}"
    )


def handle_status_update(page_id: str, value: dict):
    post_id = value.get("post_id")
    text = value.get("message", "")
    user = value.get("from", {}) or {}
    user_name = user.get("name")
    user_id = user.get("id")
    link = value.get("link")
    item = safe_lower(value.get("item"))

    post = sync_post_from_facebook(post_id, page_id)
    if link and post:
        media_type = "video" if item == "video" else "image"
        save_post_media_from_link(post, link, media_type=media_type)

    logger.info(
        f"[FEED][STATUS][UPDATE] page={page_id} post={post_id} by={user_name}({user_id}) text={text}"
    )


def handle_status_delete(page_id: str, value: dict):
    post_id = value.get("post_id")
    user = value.get("from", {}) or {}
    user_name = user.get("name")
    user_id = user.get("id")

    delete_post_from_feed(post_id, page_id)

    logger.info(
        f"[FEED][STATUS][DELETE] page={page_id} post={post_id} by={user_name}({user_id})"
    )


def handle_feed_unknown(page_id: str, value: dict):
    logger.info(f"[FEED][UNKNOWN] page={page_id} value={value}")


# -------------------------
# FEED Dispatcher (item + verb)
# -------------------------
FEED_DISPATCH = {
    ("comment", "add"): handle_comment_add,
    ("comment", "update"): handle_comment_update,
    ("comment", "delete"): handle_comment_delete,

    ("reaction", "add"): handle_reaction_add,
    ("reaction", "update"): handle_reaction_update,
    ("reaction", "delete"): handle_reaction_delete,

    ("status", "add"): handle_status_add,
    ("status", "update"): handle_status_update,
    ("status", "delete"): handle_status_delete,

    ("photo", "add"): handle_status_add,
    ("photo", "update"): handle_status_update,
    ("photo", "delete"): handle_status_delete,
    ("video", "add"): handle_status_add,
    ("video", "update"): handle_status_update,
    ("video", "delete"): handle_status_delete,
}


def dispatch_feed(page_id: str, change: dict):
    """
    change = {'field':'feed', 'value': {...}}
    """
    value = change.get("value") or {}
    item = safe_lower(value.get("item"))
    verb = normalize_verb(value.get("verb"))

    handler = FEED_DISPATCH.get((item, verb), handle_feed_unknown)
    return handler(page_id, value)


# -------------------------
# TikTok feed handlers
# -------------------------
def _normalize_tiktok_events(payload):
    if isinstance(payload, list):
        return [p for p in payload if isinstance(p, dict)]
    if not isinstance(payload, dict):
        return []

    if isinstance(payload.get("events"), list):
        return [p for p in payload.get("events") if isinstance(p, dict)]
    if isinstance(payload.get("data"), list):
        return [p for p in payload.get("data") if isinstance(p, dict)]

    entries = payload.get("entry")
    if isinstance(entries, list):
        events = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            changes = entry.get("changes")
            if isinstance(changes, list):
                for change in changes:
                    if isinstance(change, dict):
                        events.append(change)
            else:
                events.append(entry)
        if events:
            return events

    return [payload]


def _coalesce(*values):
    for value in values:
        if value not in (None, "", []):
            return value
    return None


def _tiktok_event_action(event_type: str, value: dict):
    action = normalize_verb(
        _coalesce(
            value.get("verb"),
            value.get("action"),
            value.get("op"),
        )
    )
    if action != "unknown":
        return action

    event_text = f"{event_type} {_coalesce(value.get('action'), value.get('op'), '')}".lower()
    if any(word in event_text for word in ("delete", "remove")):
        return "delete"
    if any(word in event_text for word in ("update", "edit")):
        return "update"
    return "add"


def dispatch_tiktok_feed(payload: dict):
    events = _normalize_tiktok_events(payload)
    for raw_event in events:
        value = {}
        content_payload = {}
        content_raw = raw_event.get("content")
        if isinstance(content_raw, str):
            try:
                parsed = json.loads(content_raw)
                if isinstance(parsed, dict):
                    content_payload = parsed
            except Exception:
                content_payload = {}
        elif isinstance(content_raw, dict):
            content_payload = content_raw

        if isinstance(raw_event.get("value"), dict):
            value.update(raw_event.get("value"))
        if isinstance(raw_event.get("data"), dict):
            value.update(raw_event.get("data"))
        if content_payload:
            value.update(content_payload)
        value.update(raw_event)

        event_type = safe_lower(
            _coalesce(
                raw_event.get("event"),
                raw_event.get("event_type"),
                raw_event.get("type"),
                value.get("event"),
                value.get("event_type"),
                value.get("type"),
                value.get("item"),
            )
        )
        action = _tiktok_event_action(event_type, value)

        comment_data = value.get("comment") if isinstance(value.get("comment"), dict) else {}
        user = (
            value.get("from")
            if isinstance(value.get("from"), dict)
            else value.get("user")
            if isinstance(value.get("user"), dict)
            else value.get("author")
            if isinstance(value.get("author"), dict)
            else {}
        )
        actor_id = _coalesce(
            user.get("id"),
            user.get("open_id"),
            value.get("user_id"),
            value.get("actor_id"),
            comment_data.get("user_id"),
        )
        actor_name = _coalesce(
            user.get("name"),
            user.get("display_name"),
            value.get("user_name"),
            value.get("username"),
            comment_data.get("user_name"),
        )
        account_open_id = _coalesce(
            value.get("owner_open_id"),
            value.get("target_open_id"),
            value.get("creator_open_id"),
            value.get("account_open_id"),
            value.get("open_id"),
            value.get("user_openid"),
        )

        post_id = _coalesce(
            value.get("post_id"),
            value.get("video_id"),
            value.get("item_id"),
            value.get("share_id"),
            (value.get("video") or {}).get("id") if isinstance(value.get("video"), dict) else None,
            comment_data.get("video_id"),
            comment_data.get("item_id"),
        )

        is_comment_event = (
            "comment" in event_type
            or safe_lower(value.get("item")) == "comment"
            or bool(comment_data)
            or bool(value.get("comment_id"))
        )
        is_reaction_event = (
            any(word in event_type for word in ("like", "reaction"))
            or safe_lower(value.get("item")) in {"like", "reaction"}
            or bool(value.get("reaction_type"))
        )

        if is_comment_event:
            comment_id = _coalesce(
                value.get("comment_id"),
                comment_data.get("id"),
                comment_data.get("comment_id"),
                value.get("id"),
            )
            text = _coalesce(
                value.get("text"),
                value.get("message"),
                comment_data.get("text"),
                comment_data.get("message"),
                "",
            )
            if action == "delete":
                delete_comment(
                    post_id,
                    comment_id,
                    platform="tiktok",
                    platform_user_id=account_open_id,
                )
            elif action == "update":
                update_comment(
                    post_id,
                    comment_id,
                    text=text,
                    commenter_id=actor_id,
                    commenter_name=actor_name,
                    platform="tiktok",
                    platform_user_id=account_open_id,
                )
            else:
                create_comment(
                    post_id=post_id,
                    comment_id=comment_id,
                    text=text,
                    commenter_id=actor_id,
                    commenter_name=actor_name,
                    platform="tiktok",
                    platform_user_id=account_open_id,
                )
            logger.info(
                "[TIKTOK][COMMENT][%s] post=%s comment=%s by=%s(%s)",
                action.upper(),
                post_id,
                comment_id,
                actor_name,
                actor_id,
            )
            continue

        if is_reaction_event:
            reaction_type = _coalesce(
                value.get("reaction_type"),
                value.get("reaction"),
                value.get("item"),
                "LIKE",
            )
            if action == "delete":
                delete_reaction(
                    post_id,
                    reaction_type,
                    actor_id,
                    platform="tiktok",
                    platform_user_id=account_open_id,
                )
            elif action == "update":
                update_reaction(
                    post_id,
                    reaction_type,
                    actor_id,
                    platform="tiktok",
                    platform_user_id=account_open_id,
                )
            else:
                create_reaction(
                    post_id,
                    reaction_type,
                    actor_id,
                    actor_name,
                    platform="tiktok",
                    platform_user_id=account_open_id,
                )
            logger.info(
                "[TIKTOK][REACTION][%s] post=%s reaction=%s by=%s(%s)",
                action.upper(),
                post_id,
                reaction_type,
                actor_name,
                actor_id,
            )
            continue

        logger.info("[TIKTOK][UNKNOWN] event=%s payload=%s", event_type or "unknown", raw_event)


# -------------------------
# Messaging handlers
# -------------------------
def handle_messaging_text(page_id: str, sender_id: str, event: dict):
    msg = event.get("message", {}) or {}
    text = msg.get("text", "")
    attachments = msg.get("attachments") or []
    message_id = msg.get("mid")
    if msg.get("is_echo"):
        return
    handle_message(page_id, sender_id, text, attachments, message_id=message_id)
    logger.info(f"[MSG][TEXT] page={page_id} sender={sender_id} text={text} attachments={bool(attachments)}")


def handle_messaging_postback(page_id: str, sender_id: str, event: dict):
    postback = event.get("postback", {}) or {}
    payload = postback.get("payload")
    title = postback.get("title")
    text = title or payload or ""
    if text:
        handle_message(page_id, sender_id, text, [])
    logger.info(f"[MSG][POSTBACK] page={page_id} sender={sender_id} payload={payload} title={title}")


def handle_messaging_delivery(page_id: str, sender_id: str, event: dict):
    delivery = event.get("delivery", {}) or {}
    mids = delivery.get("mids")
    watermark = delivery.get("watermark")
    mark_messages_delivered(page_id, sender_id, mids or [])
    logger.info(f"[MSG][DELIVERY] page={page_id} sender={sender_id} mids={mids} watermark={watermark}")


def handle_messaging_read(page_id: str, sender_id: str, event: dict):
    read = event.get("read", {}) or {}
    watermark = read.get("watermark")
    mark_messages_read(page_id, sender_id, watermark)
    logger.info(f"[MSG][READ] page={page_id} sender={sender_id} watermark={watermark}")


def handle_messaging_unknown(page_id: str, sender_id: str, event: dict):
    logger.info(f"[MSG][UNKNOWN] page={page_id} sender={sender_id} event={event}")


MESSAGING_DISPATCH = {
    "message": handle_messaging_text,
    "postback": handle_messaging_postback,
    "delivery": handle_messaging_delivery,
    "read": handle_messaging_read,
}


def dispatch_messaging(page_id: str, event: dict):
    if "delivery" in event or "read" in event:
        user_id = (event.get("recipient") or {}).get("id")
    else:
        user_id = (event.get("sender") or {}).get("id")

    if not user_id:
        logger.warning(f"[MSG] sender missing: {event}")
        return

    for key, fn in MESSAGING_DISPATCH.items():
        if key in event:
            return fn(page_id, user_id, event)

    return handle_messaging_unknown(page_id, user_id, event)


# -------------------------
# WhatsApp handlers
# -------------------------
def _get_or_create_whatsapp_social_account(wa_account):
    social = SocialAccount.objects.filter(
        user=wa_account.user,
        platform="whatsapp",
    ).first()
    if social:
        return social

    token = getattr(settings, "WHATSAPP_SYSTEM_TOKEN", "") or ""
    return SocialAccount.objects.create(
        user=wa_account.user,
        platform="whatsapp",
        user_access_token=token,
        long_lived_token=token,
        name=wa_account.business_name or "WhatsApp Business",
    )


def _build_conversation_history(conversation):
    role_map = {
        "customer": "user",
        "bot": "assistant",
        "seller": "user",
    }
    history = []
    for msg in conversation.messages.all().order_by("created_at"):
        history.append(
            {
                "role": role_map.get(msg.sender_type, "user"),
                "content": msg.text or "",
                "time": msg.created_at.isoformat(),
            }
        )
    return history


def _store_whatsapp_message(
    conversation,
    sender_type,
    text="",
    message_id=None,
    attachments=None,
    is_sent=False,
    is_read=False,
    sender_name=None,
    sender_metadata=None,
):
    message = Message.objects.create(
        conversation=conversation,
        platform="whatsapp",
        sender_type=sender_type,
        text=text or "",
        attachments=attachments or [],
        message_id=message_id,
        is_sent=is_sent,
        is_read=is_read,
        sender_name=sender_name,
        sender_metadata=sender_metadata or {},
    )
    conversation.last_message_at = timezone.now()
    conversation.save(update_fields=["last_message_at"])
    send_to_socket(conversation, message)
    return message


def _process_whatsapp_statuses(social_account, statuses):
    for status_payload in statuses or []:
        recipient_id = status_payload.get("recipient_id")
        if not recipient_id:
            continue
        message_id = status_payload.get("id")
        state = (status_payload.get("status") or "").lower()

        conversation = Conversation.objects.filter(
            platform="whatsapp",
            social_account=social_account,
            external_user_id=recipient_id,
        ).first()
        if not conversation:
            continue

        qs = Message.objects.filter(conversation=conversation)
        if message_id:
            qs = qs.filter(message_id=message_id)

        updates = {}
        if state in {"sent", "delivered", "read"}:
            updates["is_sent"] = True
        if state == "read":
            updates["is_read"] = True
        if updates:
            qs.update(**updates)


def _process_whatsapp_messages(social_account, wa_account, phone_number_id, value):
    contacts = {
        contact.get("wa_id"): contact
        for contact in (value.get("contacts") or [])
        if contact.get("wa_id")
    }

    for payload in value.get("messages", []) or []:
        sender_wa_id = payload.get("from")
        if not sender_wa_id:
            continue

        incoming_message_id = payload.get("id")
        msg_type = payload.get("type")
        text = ""
        attachments = []
        if msg_type == "text":
            text = ((payload.get("text") or {}).get("body") or "").strip()
        else:
            attachments = [payload]

        contact = contacts.get(sender_wa_id) or {}
        profile_name = (contact.get("profile") or {}).get("name") or ""
        metadata = {
            "wa_id": sender_wa_id,
            "contact": contact,
        }

        conversation, _ = Conversation.objects.get_or_create(
            platform="whatsapp",
            social_account=social_account,
            external_user_id=sender_wa_id,
            defaults={
                "external_username": profile_name or sender_wa_id,
                "page_id": phone_number_id,
                "personal_info": metadata,
            },
        )

        if profile_name and conversation.external_username != profile_name:
            conversation.external_username = profile_name
            conversation.save(update_fields=["external_username"])

        if incoming_message_id and Message.objects.filter(
            conversation=conversation,
            message_id=incoming_message_id,
            sender_type="customer",
        ).exists():
            continue

        _store_whatsapp_message(
            conversation=conversation,
            sender_type="customer",
            text=text,
            attachments=attachments,
            message_id=incoming_message_id,
            is_sent=True,
            sender_name=profile_name or sender_wa_id,
            sender_metadata=metadata,
        )

        if not text or not conversation.is_bot_active:
            continue

        history = _build_conversation_history(conversation)
        bot_payload = chatbot_reply(
            text,
            history,
            [],
            owner_user_id=wa_account.user_id,
            source_platform=conversation.platform,
        )
        reply_text = ((bot_payload or {}).get("reply") or "").strip()
        if not reply_text:
            continue

        send_resp = send_whatsapp_text(
            phone_number_id,
            sender_wa_id,
            reply_text,
            access_token=(
                social_account.long_lived_token
                or social_account.user_access_token
                or getattr(settings, "WHATSAPP_SYSTEM_TOKEN", "")
            ),
        )
        message_ids = send_resp.get("messages") or []
        outgoing_id = message_ids[0].get("id") if message_ids else None
        is_sent = bool(send_resp) and not send_resp.get("error")

        _store_whatsapp_message(
            conversation=conversation,
            sender_type="bot",
            text=reply_text,
            message_id=outgoing_id,
            is_sent=is_sent,
            sender_name="Bot",
            sender_metadata={"provider_response": send_resp},
        )


def dispatch_whatsapp_messages(entry: dict, change: dict):
    value = change.get("value") or {}
    metadata = value.get("metadata") or {}
    phone_number_id = metadata.get("phone_number_id")
    if not phone_number_id:
        logger.warning("[WA] phone_number_id missing in webhook payload: %s", value)
        return

    wa_account = WhatsAppBusinessAccount.objects.select_related("user").filter(
        phone_number_id=phone_number_id
    ).first()
    if not wa_account:
        logger.warning(
            "[WA] Unknown phone_number_id=%s entry_id=%s",
            phone_number_id,
            entry.get("id"),
        )
        return

    social_account = _get_or_create_whatsapp_social_account(wa_account)
    _process_whatsapp_statuses(social_account, value.get("statuses") or [])
    _process_whatsapp_messages(social_account, wa_account, phone_number_id, value)
