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

def upload_unpublished_images(page, image_urls):
    media_ids = []

    for url in image_urls:
        photo = page.create_photo(
            params={
                "url": url,
                "published": False
            }
        )
        media_ids.append({"media_fbid": photo["id"]})

    return media_ids



def publish_fb_post( page_id, page_access_token, message, image_urls, publish=False):
    if not publish:
        return None
    init_facebook(app_id, app_secret, page_access_token)

    page = Page(page_id)

    attached_media = upload_unpublished_images(page, image_urls)

    response = page.create_feed(
        params={
            "message": message,
            "attached_media": attached_media
        }
    )

    return response.get("id")

