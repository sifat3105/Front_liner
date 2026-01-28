from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.page import Page
from facebook_business.adobjects.objectparser import ObjectParser
from facebook_business.adobjects.comment import Comment
from facebook_business.adobjects.post import Post
from django.conf import settings


app_id = settings.FACEBOOK_APP_ID
app_secret = settings.FACEBOOK_APP_SECRET

def init_facebook(app_id, page_access_token):
    FacebookAdsApi.init(
        app_id=app_id,
        app_secret=app_secret,
        access_token=page_access_token
    )

def upload_unpublished_media(page, media_urls, title):
    """
    Upload images or videos unpublished and return media IDs
    """
    media_ids = []
    video_ids = []
    for url in media_urls:
        if url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.tiff', '.heif', '.webp')):
            # Image upload
            photo = page.create_photo(
                params={
                    "url": url,
                    "published": False
                }
            )
            media_ids.append({"media_fbid": photo["id"]})

        elif url.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
            video = page.create_video(
                params={
                    "file_url": url,
                    "title": title,
                    "description": None,
                    "published": True
                }
            )
            video_ids.append(video["id"])

        else:
            print(f"Unsupported media format: {url}")

    return media_ids, video_ids



def publish_fb_post( page_id, page_access_token, message, image_urls, publish=False):
    if not publish:
        return None
    init_facebook(app_id,  page_access_token)

    page = Page(page_id)

    attached_media, video_ids = upload_unpublished_media(page, image_urls, message)

    response = page.create_feed(
        params={
            "message": message,
            "attached_media": attached_media
        }
    )

    return response.get("id")



def get_post_reactions(post):

    reactions = post.get_reactions(
        fields=["type"],
        params={"summary": True, "limit": 0}
    )

    total_reactions = reactions._summary.get("total_count", 0)

    return total_reactions



def get_post_insights(page_access_token, post_id, comments_limit=25):
    print(page_access_token)

    init_facebook(app_id,  page_access_token)

    post = Post("920570247807198_122112296151164381")
    
    # 2) Comments list + count (summary)
    try:
        comments_edge = post.get_comments(
            fields=[
                "id",
                "message",
                "created_time",
                "from{name,id}",   #
                "like_count",
            ],
            params={"summary": True, "limit": comments_limit, "order": "reverse_chronological"},
        )
        
    except Exception as e:
        print(f"Error fetching comments: {e}")

    comments_count = 0
    try:
        comments_count = comments_edge._summary.get("total_count", 0)
    except Exception:
        comments_count = 0

    comments = []
    for c in comments_edge:
        frm = c.get("from") or {}
        comments.append({
            "id": c.get("id"),
            "message": c.get("message"),
            "created_time": c.get("created_time"),
            "commenter_id": frm.get("id"),
            "commenter_name": frm.get("name"),
            "like_count": c.get("like_count", 0),
        })

    return {
        "post_id": post_id,
        "reactions_count": get_post_reactions(post),
        "comments_count": comments_count,
        "comments": comments,
    }