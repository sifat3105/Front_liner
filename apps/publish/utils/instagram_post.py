import requests


def post_instagram_single_media(ig_user_id, access_token, media_url, caption ):
    print(media_url)
    print(caption)
    print(access_token)
    print(ig_user_id)
    create_url = f"https://graph.facebook.com/v19.0/{ig_user_id}/media"
    media_data = {
        "caption": caption,
        "access_token": access_token,
    }

    if media_url.lower().endswith((".mp4", ".mov")):
        media_data["video_url"] = media_url
    else:
        media_data["image_url"] = media_url

    create_res = requests.post(create_url, data=media_data).json()

    if "id"  in create_res:
        return create_res["id"]
    else:
        return None

def create_image_container(ig_user_id, media_url, access_token):
    url = f"https://graph.facebook.com/v19.0/{ig_user_id}/media"
    media_data = {
        "access_token": access_token,
        "is_carousel_item": True,
    }
    if media_url.lower().endswith((".mp4", ".mov")):
        media_data["video_url"] = media_url
    else:
        media_data["image_url"] = media_url
    
    res = requests.post(url, data=media_data).json()
    return res["id"]

def create_carousel_container(ig_user_id, children_ids, caption, access_token):
    url = f"https://graph.facebook.com/v19.0/{ig_user_id}/media"
    res = requests.post(url, data={
        "media_type": "CAROUSEL",
        "children": ",".join(children_ids),
        "caption": caption,
        "access_token": access_token,
    }).json()
    return res["id"]


def create_ig_post(ig_user_id, access_token, caption, media_urls, publish=False):

    if len(media_urls) == 1:
        draft_id = post_instagram_single_media(ig_user_id, access_token, media_urls[0], caption)
        print(draft_id)
        if publish:
            post_id = publish_ig_post(ig_user_id, draft_id, access_token)
            return post_id
        else:
            return draft_id
    else:
        child_ids = [
            create_image_container(ig_user_id, img, access_token)
            for img in media_urls
        ]
        carousel_id = create_carousel_container(
            ig_user_id,
            child_ids,
            caption,
            access_token
        )

        if publish:
            post_id = publish_ig_post(ig_user_id, carousel_id, access_token)
            return post_id
        return carousel_id


def publish_ig_post(ig_user_id, creation_id, access_token):
    url = f"https://graph.facebook.com/v19.0/{ig_user_id}/media_publish"
    return requests.post(url, data={
        "creation_id": creation_id,
        "access_token": access_token
    }).json()


