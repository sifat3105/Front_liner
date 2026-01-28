import logging

from apps.chat.utils import handle_message, mark_messages_delivered, mark_messages_read
from apps.publish.services.post_dispatch_feed import (
    create_comment,
    update_comment,
    delete_comment,
    create_reaction,
    update_reaction,
    delete_reaction,
    sync_post_from_facebook,
    delete_post_from_feed,
    save_post_media_from_link,
)

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
    
    update_reaction(post_id, reaction_type, user_id,)
    
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
