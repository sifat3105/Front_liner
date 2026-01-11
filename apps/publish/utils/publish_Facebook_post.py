from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.page import Page
from django.conf import settings


app_id = settings.FACEBOOK_APP_ID
app_secret = settings.FACEBOOK_APP_SECRET

def init_facebook(app_id, app_secret, page_access_token):
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
    init_facebook(app_id, app_secret, page_access_token)

    page = Page(page_id)

    attached_media, video_ids = upload_unpublished_media(page, image_urls, message)

    response = page.create_feed(
        params={
            "message": message,
            "attached_media": attached_media
        }
    )

    return response.get("id"), video_ids

