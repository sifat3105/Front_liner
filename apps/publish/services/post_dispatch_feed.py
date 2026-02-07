from typing import Dict, Any, Optional
import hashlib
import os
from urllib.parse import urlparse
import requests
from django.utils.dateparse import parse_datetime
from django.core.files.base import ContentFile
from ..models import SocialPost, Comment, SubComment, Reaction, PostMediaFile
from apps.social.models import FacebookPage, SocialAccount, SocialPlatform


def _normalize_post_id(post_id):
    if isinstance(post_id, (list, tuple)) and post_id:
        return str(post_id[0])
    if post_id is None:
        return None
    return str(post_id)


def get_post(post_id):
    post_id = _normalize_post_id(post_id)
    if not post_id:
        return None

    qs = SocialPost.objects.filter(post_ids__contains=[{"post_id": post_id}])
    post = qs.first()
    if post:
        return post

    qs = SocialPost.objects.filter(post_ids__contains=[{"post_id": [post_id]}])
    post = qs.first()
    if post:
        return post

    for candidate in SocialPost.objects.exclude(post_ids=[]).only("id", "post_ids"):
        for item in candidate.post_ids or []:
            pid = item.get("post_id")
            if isinstance(pid, list):
                if post_id in [str(x) for x in pid]:
                    return candidate
            elif pid is not None and str(pid) == post_id:
                return candidate
    

    return None


def get_or_create_post(post_id, page_id=None, platform="facebook", platform_user_id=None):
    post = get_post(post_id)
    if post:
        return post

    post_id = _normalize_post_id(post_id)
    if not post_id:
        return None
    platform = (platform or "facebook").lower()

    if platform == "facebook":
        if not page_id:
            return None
        try:
            page = FacebookPage.objects.select_related("user").get(page_id=page_id, is_active=True)
        except FacebookPage.DoesNotExist:
            return None

        fetched = fetch_facebook_post_details(post_id, page.page_access_token)
        if not fetched.get("success"):
            return None

        data = fetched.get("data") or {}
        caption = data.get("message") or ""
        created_time = parse_datetime(data.get("created_time") or "")

        post = SocialPost.objects.create(
            author=page.user,
            title=caption[:80] if caption else "",
            caption=caption,
            is_published=True,
            post_ids=[{"status": "success", "post_id": [post_id], "platform": "facebook"}],
            page_access_token=page.page_access_token,
            published_at=created_time,
        )

        social_platform = SocialPlatform.objects.filter(name="facebook").first()
        if social_platform:
            post.platforms.add(social_platform)

        for link, media_type in _extract_media_links_from_post(data):
            save_post_media_from_link(post, link, media_type=media_type)
        return post

    if platform == "tiktok":
        if not platform_user_id:
            return None
        account = (
            SocialAccount.objects.select_related("user")
            .filter(platform="tiktok", tk_user_id=str(platform_user_id))
            .first()
        )
        if not account:
            return None

        post = SocialPost.objects.create(
            author=account.user,
            title="",
            caption="",
            is_published=True,
            post_ids=[{"status": "success", "post_id": post_id, "platform": "tiktok"}],
        )
        social_platform = SocialPlatform.objects.filter(name="tiktok").first()
        if social_platform:
            post.platforms.add(social_platform)
        return post

    return None


def sync_post_from_facebook(post_id, page_id):
    post_id = _normalize_post_id(post_id)
    if not post_id or not page_id:
        return None

    page = (
        FacebookPage.objects.filter(page_id=page_id, is_active=True)
        .select_related("user")
        .first()
    )
    if not page:
        return None

    fetched = fetch_facebook_post_details(post_id, page.page_access_token)
    if not fetched.get("success"):
        return None

    data = fetched.get("data") or {}
    caption = data.get("message") or ""
    created_time = parse_datetime(data.get("created_time") or "")

    post = get_post(post_id)
    if not post:
        post = SocialPost.objects.create(
            author=page.user,
            title=caption[:80] if caption else "",
            caption=caption,
            is_published=True,
            post_ids=[{"status": "success", "post_id": [post_id], "platform": "facebook"}],
            page_access_token=page.page_access_token,
            published_at=created_time,
        )

        platform = SocialPlatform.objects.filter(name="facebook").first()
        if platform:
            post.platforms.add(platform)
        for link, media_type in _extract_media_links_from_post(data):
            save_post_media_from_link(post, link, media_type=media_type)
        return post

    update_fields = []
    if caption != post.caption:
        post.caption = caption
        update_fields.append("caption")
        post.title = caption[:80] if caption else ""
        update_fields.append("title")
    if created_time and created_time != post.published_at:
        post.published_at = created_time
        update_fields.append("published_at")
    if not post.is_published:
        post.is_published = True
        update_fields.append("is_published")
    if page.page_access_token and page.page_access_token != post.page_access_token:
        post.page_access_token = page.page_access_token
        update_fields.append("page_access_token")

    if update_fields:
        post.save(update_fields=update_fields)

    if not post.platforms.filter(name="facebook").exists():
        platform = SocialPlatform.objects.filter(name="facebook").first()
        if platform:
            post.platforms.add(platform)

    if not post.media.exists():
        for link, media_type in _extract_media_links_from_post(data):
            save_post_media_from_link(post, link, media_type=media_type)

    return post


def delete_post_from_feed(post_id, page_id=None):
    post = get_post(post_id)
    if not post and page_id:
        post = get_or_create_post(post_id, page_id=page_id)
    if not post:
        return False

    post.delete()
    return True


def save_post_media_from_link(post, link, media_type="image"):
    if not post or not link:
        return None

    parsed = urlparse(link)
    ext = os.path.splitext(parsed.path)[1].lower()
    if not ext:
        ext = ".mp4" if media_type == "video" else ".jpg"

    token = hashlib.md5(link.encode("utf-8")).hexdigest()[:12]
    filename = f"fb_{post.id}_{token}{ext}"

    if PostMediaFile.objects.filter(post=post, file__endswith=filename).exists():
        return None

    r = requests.get(link, timeout=20)
    if r.status_code != 200:
        return None

    return PostMediaFile.objects.create(
        post=post,
        file=ContentFile(r.content, name=filename),
        media_type=media_type,
    )

def create_comment(
    post_id,
    comment_id,
    text,
    commenter_id,
    commenter_name,
    attachments=None,
    page_id=None,
    platform="facebook",
    platform_user_id=None,
):
    post = get_or_create_post(
        post_id,
        page_id=page_id,
        platform=platform,
        platform_user_id=platform_user_id,
    )
    if not post or not comment_id:
        return None
    comment, _ = Comment.objects.update_or_create(
        post=post,
        comment_id=comment_id,
        defaults={
            "text": text or "",
            "attachments": attachments or [],
            "commenter_id": commenter_id or "",
            "commenter_name": commenter_name or "",
            "platform": platform,
        },
    )
    return comment


def update_comment(
    post_id,
    comment_id,
    text=None,
    commenter_id=None,
    commenter_name=None,
    attachments=None,
    page_id=None,
    platform="facebook",
    platform_user_id=None,
):
    post = get_or_create_post(
        post_id,
        page_id=page_id,
        platform=platform,
        platform_user_id=platform_user_id,
    )
    if not post:
        return None

    comment = Comment.objects.filter(post=post, comment_id=comment_id).first()
    if not comment:
        return None

    update_fields = []
    if text is not None:
        comment.text = text
        update_fields.append("text")
    if commenter_id is not None:
        comment.commenter_id = commenter_id
        update_fields.append("commenter_id")
    if commenter_name is not None:
        comment.commenter_name = commenter_name
        update_fields.append("commenter_name")
    if attachments is not None:
        comment.attachments = attachments
        update_fields.append("attachments")
    if comment.platform != platform:
        comment.platform = platform
        update_fields.append("platform")

    if update_fields:
        comment.save(update_fields=update_fields)

    return comment


def _get_or_create_parent_comment(post, parent_comment_id, platform="facebook"):
    if not parent_comment_id:
        return None
    parent, _ = Comment.objects.get_or_create(
        post=post,
        comment_id=parent_comment_id,
        defaults={"platform": platform},
    )
    return parent


def create_comment_reply(
    post_id,
    parent_comment_id,
    sub_comment_id,
    text,
    commenter_id,
    commenter_name,
    page_id=None,
    platform="facebook",
    platform_user_id=None,
):
    post = get_or_create_post(
        post_id,
        page_id=page_id,
        platform=platform,
        platform_user_id=platform_user_id,
    )
    if not post or not parent_comment_id or not sub_comment_id:
        return None

    parent = _get_or_create_parent_comment(post, parent_comment_id, platform=platform)
    if not parent:
        return None

    sub_comment, _ = SubComment.objects.update_or_create(
        comment=parent,
        sub_comment_id=sub_comment_id,
        defaults={
            "text": text or "",
            "commenter_id": commenter_id or "",
            "commenter_name": commenter_name or "",
            "platform": platform,
        },
    )
    return sub_comment


def update_comment_reply(
    post_id,
    parent_comment_id,
    sub_comment_id,
    text=None,
    commenter_id=None,
    commenter_name=None,
    page_id=None,
    platform="facebook",
    platform_user_id=None,
):
    post = get_or_create_post(
        post_id,
        page_id=page_id,
        platform=platform,
        platform_user_id=platform_user_id,
    )
    if not post or not parent_comment_id or not sub_comment_id:
        return None

    parent = _get_or_create_parent_comment(post, parent_comment_id, platform=platform)
    if not parent:
        return None

    sub_comment = SubComment.objects.filter(
        comment=parent,
        sub_comment_id=sub_comment_id,
    ).first()
    if not sub_comment:
        return create_comment_reply(
            post_id=post_id,
            parent_comment_id=parent_comment_id,
            sub_comment_id=sub_comment_id,
            text=text or "",
            commenter_id=commenter_id,
            commenter_name=commenter_name,
            page_id=page_id,
            platform=platform,
            platform_user_id=platform_user_id,
        )

    update_fields = []
    if text is not None:
        sub_comment.text = text
        update_fields.append("text")
    if commenter_id is not None:
        sub_comment.commenter_id = commenter_id
        update_fields.append("commenter_id")
    if commenter_name is not None:
        sub_comment.commenter_name = commenter_name
        update_fields.append("commenter_name")
    if sub_comment.platform != platform:
        sub_comment.platform = platform
        update_fields.append("platform")

    if update_fields:
        sub_comment.save(update_fields=update_fields)
    return sub_comment


def delete_comment_reply(
    post_id,
    parent_comment_id,
    sub_comment_id,
    page_id=None,
    platform="facebook",
    platform_user_id=None,
):
    post = get_or_create_post(
        post_id,
        page_id=page_id,
        platform=platform,
        platform_user_id=platform_user_id,
    )
    if not post or not parent_comment_id or not sub_comment_id:
        return False
    parent = Comment.objects.filter(post=post, comment_id=parent_comment_id).first()
    if not parent:
        return False

    deleted, _ = SubComment.objects.filter(
        comment=parent,
        sub_comment_id=sub_comment_id,
    ).delete()
    return deleted > 0


def delete_comment(post_id, comment_id, page_id=None, platform="facebook", platform_user_id=None):
    post = get_or_create_post(
        post_id,
        page_id=page_id,
        platform=platform,
        platform_user_id=platform_user_id,
    )
    if not post:
        return False

    comment = Comment.objects.filter(post=post, comment_id=comment_id).first()
    if not comment:
        return False

    comment.delete()
    return True


def create_reaction(
    post_id,
    reaction,
    reactor_id,
    reactor_name,
    page_id=None,
    platform="facebook",
    platform_user_id=None,
):
    post = get_or_create_post(
        post_id,
        page_id=page_id,
        platform=platform,
        platform_user_id=platform_user_id,
    )
    if not post or not reactor_id:
        return None

    data, _ = Reaction.objects.update_or_create(
        post=post,
        reactor_id=reactor_id,
        defaults={
            "reaction": reaction or "",
            "reactor_name": reactor_name or "",
            "platform": platform,
        },
    )
    return data
    
    
    
def update_reaction(
    post_id,
    reaction_type,
    reactor_id,
    page_id=None,
    platform="facebook",
    platform_user_id=None,
):
    post = get_or_create_post(
        post_id,
        page_id=page_id,
        platform=platform,
        platform_user_id=platform_user_id,
    )
    if not post or not reactor_id:
        return None
    
    reaction_obj = Reaction.objects.filter(
        post=post,
        reactor_id=reactor_id,
        platform=platform,
    ).first()
    if not reaction_obj:
        return create_reaction(
            post_id,
            reaction_type,
            reactor_id,
            reactor_name="",
            page_id=page_id,
            platform=platform,
            platform_user_id=platform_user_id,
        )
    
    reaction_obj.reaction = reaction_type
    update_fields = ["reaction"]
    if reaction_obj.platform != platform:
        reaction_obj.platform = platform
        update_fields.append("platform")
    reaction_obj.save(update_fields=update_fields)
    return reaction_obj


def delete_reaction(
    post_id,
    reaction,
    reactor_id,
    page_id=None,
    platform="facebook",
    platform_user_id=None,
):
    post = get_or_create_post(
        post_id,
        page_id=page_id,
        platform=platform,
        platform_user_id=platform_user_id,
    )
    if not post or not reactor_id:
        return False

    qs = Reaction.objects.filter(
        post=post,
        reactor_id=reactor_id,
        platform=platform,
    )
    if reaction:
        qs = qs.filter(reaction=reaction)
    deleted, _ = qs.delete()
    return deleted > 0


def fetch_facebook_post_details(
    post_id: str,
    page_access_token: str,
    api_version: str = "v19.0",
) -> Dict[str, Any]:
    """
    Fetch real post info from Facebook Graph.
    """
    fields = (
        "id,message,created_time,permalink_url,from{name,id},"
        "attachments{media_type,media,url,subattachments}"
    )
    url = f"https://graph.facebook.com/{api_version}/{post_id}"

    r = requests.get(url, params={"fields": fields, "access_token": page_access_token}, timeout=15)

    try:
        data = r.json()
    except Exception:
        return {"success": False, "error": "Invalid JSON from Facebook", "status_code": r.status_code}

    if r.status_code != 200 or "error" in data:
        return {"success": False, "error": data.get("error", data), "status_code": r.status_code}

    return {"success": True, "data": data}


def _extract_media_links_from_post(data):
    links = []
    attachments = (data or {}).get("attachments", {}) or {}
    items = attachments.get("data") or []
    for att in items:
        media = att.get("media") or {}
        img = media.get("image") or {}
        if img.get("src"):
            links.append((img.get("src"), "image"))
        if att.get("media_type") == "video" and att.get("url"):
            links.append((att.get("url"), "video"))

        sub = (att.get("subattachments") or {}).get("data") or []
        for s in sub:
            smedia = s.get("media") or {}
            simg = smedia.get("image") or {}
            if simg.get("src"):
                links.append((simg.get("src"), "image"))
            if s.get("media_type") == "video" and s.get("url"):
                links.append((s.get("url"), "video"))

    return links
