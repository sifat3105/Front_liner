from apps.social.models import SocialAccount, FacebookPage, InstagramAccount
from ..utils.publish_Facebook_post import publish_fb_post
from ..utils.instagram_post import create_ig_post, publish_ig_post
import json


def format_hashtags(raw_hashtags):
    if not raw_hashtags:
        return ""

    # Case 1: ['["test1","test2"]']
    if isinstance(raw_hashtags, list) and len(raw_hashtags) == 1 and isinstance(raw_hashtags[0], str):
        raw_hashtags = raw_hashtags[0]

    # Case 2: '["test1","test2"]'
    if isinstance(raw_hashtags, str):
        raw_hashtags = json.loads(raw_hashtags)

    return " ".join(f"#{tag.strip()}" for tag in raw_hashtags)


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
                raise Exception("TikTok publishing not supported yet")

            else:
                raise Exception("Unsupported platform")

            post_ids.append({
                "platform": platform.name,
                "post_id": post_id,
                "status": "success"
            })

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
                publish_fb_post(
                    page_id=page.page_id,
                    page_access_token=page.page_access_token,
                    message=post.caption,
                    image_urls=post.media.all().values_list("file", flat=True),
                    publish=True
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
                    status = False
                    print("Instagram post not found")
                publish_ig_post(ig.ig_user_id, ig_post_id, account.long_lived_token)
                
            elif platform.name == "tiktok":
                raise Exception("TikTok publishing not supported yet")

            else:
                raise Exception("Unsupported platform")
            return True
        except Exception as e:
            print(e)
