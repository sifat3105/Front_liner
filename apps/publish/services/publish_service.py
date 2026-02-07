import json

from django.conf import settings

from apps.social.models import FacebookPage, InstagramAccount, SocialAccount
from ..utils.instagram_post import create_ig_post, publish_ig_post
from ..utils.publish_Facebook_post import publish_fb_post
from ..utils.tiktok_post import create_tiktok_post


def format_hashtags(raw_hashtags):
    if not raw_hashtags:
        return ""

    # Case 1: ['["test1","test2"]']
    if isinstance(raw_hashtags, list) and len(raw_hashtags) == 1 and isinstance(raw_hashtags[0], str):
        raw_hashtags = raw_hashtags[0]

    # Case 2: '["test1","test2"]'
    if isinstance(raw_hashtags, str):
        try:
            raw_hashtags = json.loads(raw_hashtags)
        except Exception:
            raw_hashtags = [raw_hashtags]

    return " ".join(
        f"#{tag.strip().lstrip('#')}"
        for tag in raw_hashtags
        if isinstance(tag, str) and tag.strip()
    )


def _resolve_tiktok_token(account):
    return account.access_token or account.long_lived_token or account.user_access_token


def _resolve_media_urls(post):
    urls = []
    for media in post.media.all():
        file_url = media.file.url
        if file_url.startswith("http://") or file_url.startswith("https://"):
            urls.append(file_url)
            continue
        media_base = settings.MEDIA_URL.rstrip("/")
        urls.append(f"{media_base}/{file_url.lstrip('/')}")
    return urls


def _replace_or_append_post_id(post_ids, platform_name, post_id, extra=None):
    extra = extra or {}
    updated = []
    replaced = False
    for item in post_ids or []:
        if item.get("platform") == platform_name:
            payload = {
                "platform": platform_name,
                "post_id": post_id,
                "status": "success",
            }
            payload.update(extra)
            updated.append(payload)
            replaced = True
        else:
            updated.append(item)
    if not replaced:
        payload = {
            "platform": platform_name,
            "post_id": post_id,
            "status": "success",
        }
        payload.update(extra)
        updated.append(payload)
    return updated


def publish_to_platforms(user, post, platforms, media_urls):
    post_ids = []
    hashtags = format_hashtags(post.hashtags)
    print(hashtags)
    caption = F"""
    {post.caption}
    
    .
    .
    .
    {hashtags}
    """

    for platform in platforms:
        try:
            account = SocialAccount.objects.get(
                user=user,
                platform=platform.name
            )

            if platform.name == "facebook":
                page = FacebookPage.objects.filter(
                    social_account=account,
                    is_active=True
                ).first()

                if not page:
                    raise Exception("Facebook page not found")

                post_id = publish_fb_post(
                    page_id=page.page_id,
                    page_access_token=page.page_access_token,
                    message=caption,
                    image_urls=media_urls,
                    publish=post.is_published
                )
                post.page_access_token = page.page_access_token
                post.save()
            elif platform.name == "instagram":
                ig = InstagramAccount.objects.filter(
                    user=user,
                    social_account=account,
                    is_active=True
                ).first()

                if not ig:
                    raise Exception("Instagram account not found")

                post_id = create_ig_post(
                    ig_user_id=ig.ig_user_id,
                    access_token=account.long_lived_token,
                    caption=caption,
                    media_urls=media_urls,
                    publish=post.is_published
                )

            elif platform.name == "tiktok":
                token = _resolve_tiktok_token(account)
                result = create_tiktok_post(
                    access_token=token,
                    caption=caption,
                    media_urls=media_urls,
                    publish=post.is_published,
                )
                post_id = result.get("publish_id")

            else:
                raise Exception("Unsupported platform")

            payload = {
                "platform": platform.name,
                "post_id": post_id,
                "status": "success"
            }
            if platform.name == "tiktok":
                payload["details"] = result.get("raw", {})
            post_ids.append(payload)

        except Exception as e:
            post_ids.append({
                "platform": platform.name,
                "status": "failed",
                "error": str(e)
            })

    return post_ids


def get_platform_post_id(post_ids, platform_name):
    for item in post_ids:
        if item.get("platform") == platform_name and item.get("status") == "success":
            return item.get("post_id")
    return None


def publish_post(user, post):
    publish_results = []
    all_success = True
    media_urls = _resolve_media_urls(post)
    existing_post_ids = post.post_ids or []

    for platform in post.platforms.all():
        try:
            account = SocialAccount.objects.get(
                user=user,
                platform=platform.name
            )
            if platform.name == "facebook":
                page = FacebookPage.objects.filter(
                    user=user,
                    social_account=account,
                    is_active=True
                ).first()

                if not page:
                    raise Exception("Facebook page not found")
                fb_post_id = publish_fb_post(
                    page_id=page.page_id,
                    page_access_token=page.page_access_token,
                    message=post.caption,
                    image_urls=media_urls,
                    publish=True
                )
                existing_post_ids = _replace_or_append_post_id(
                    existing_post_ids,
                    "facebook",
                    fb_post_id,
                )
            elif platform.name == "instagram":
                ig = InstagramAccount.objects.filter(
                    user=user,
                    social_account=account,
                    is_active=True
                ).first()

                if not ig:
                    raise Exception("Instagram account not found")
                ig_post_id = get_platform_post_id(post.post_ids, "instagram")
                if not ig_post_id:
                    raise Exception("Instagram draft post not found")
                ig_publish_res = publish_ig_post(ig.ig_user_id, ig_post_id, account.long_lived_token)
                published_id = (
                    ig_publish_res.get("id")
                    if isinstance(ig_publish_res, dict)
                    else ig_post_id
                )
                existing_post_ids = _replace_or_append_post_id(
                    existing_post_ids,
                    "instagram",
                    published_id,
                    extra={"draft_id": ig_post_id},
                )
                
            elif platform.name == "tiktok":
                token = _resolve_tiktok_token(account)
                result = create_tiktok_post(
                    access_token=token,
                    caption=post.caption,
                    media_urls=media_urls,
                    publish=True,
                )
                publish_id = result.get("publish_id")
                existing_post_ids = _replace_or_append_post_id(
                    existing_post_ids,
                    "tiktok",
                    publish_id,
                    extra={"details": result.get("raw", {})},
                )

            else:
                raise Exception("Unsupported platform")

            publish_results.append({
                "platform": platform.name,
                "status": "success",
            })
        except Exception as e:
            all_success = False
            publish_results.append({
                "platform": platform.name,
                "status": "failed",
                "error": str(e),
            })

    post.post_ids = existing_post_ids
    post.save(update_fields=["post_ids"])
    return {
        "success": all_success,
        "results": publish_results,
        "post_ids": existing_post_ids,
    }
