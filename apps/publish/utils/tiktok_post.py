import mimetypes
import os
import tempfile

import requests


TIKTOK_API_BASE = "https://open.tiktokapis.com"
REQUEST_TIMEOUT = 20
CHUNK_SIZE_DEFAULT = 10_000_000
CHUNK_SIZE_MIN = 5 * 1024 * 1024
CHUNK_SIZE_MAX = 64 * 1024 * 1024


def _tiktok_request(method, endpoint, access_token, **kwargs):
    headers = kwargs.pop("headers", {}) or {}
    headers.setdefault("Authorization", f"Bearer {access_token}")
    headers.setdefault("Content-Type", "application/json")
    kwargs["headers"] = headers
    kwargs.setdefault("timeout", REQUEST_TIMEOUT)
    response = requests.request(method, f"{TIKTOK_API_BASE}{endpoint}", **kwargs)
    try:
        data = response.json()
    except ValueError:
        data = {"error": {"message": "Invalid JSON response from TikTok"}}
    return response, data


def _extract_error_message(data):
    if not isinstance(data, dict):
        return "Unknown TikTok error"
    error = data.get("error") or {}
    if isinstance(error, dict):
        return (
            error.get("message")
            or error.get("description")
            or error.get("code")
            or str(error)
        )
    if data.get("message"):
        return str(data.get("message"))
    return "Unknown TikTok error"


def _is_tiktok_ok(data):
    if not isinstance(data, dict):
        return False

    error = data.get("error")
    if not error:
        return True
    if not isinstance(error, dict):
        return False

    code = str(error.get("code") or "").strip().lower()
    message = str(error.get("message") or "").strip().lower()
    if code in {"ok", "0"}:
        return True
    if message == "ok":
        return True
    return False


def _is_success_response(response, data):
    return getattr(response, "status_code", None) == 200 and _is_tiktok_ok(data)


def _extract_video_url(media_urls):
    media_urls = media_urls or []
    video_ext = (".mp4", ".mov", ".avi", ".mkv", ".webm")
    for url in media_urls:
        if isinstance(url, str) and url.lower().endswith(video_ext):
            return url
    return None


def _extract_publish_id(payload):
    data = payload.get("data") if isinstance(payload, dict) else {}
    if not isinstance(data, dict):
        return None
    return (
        data.get("publish_id")
        or data.get("post_id")
        or data.get("video_id")
        or data.get("item_id")
    )


def _extract_error_code(data):
    if not isinstance(data, dict):
        return ""
    error = data.get("error") or {}
    if isinstance(error, dict):
        return str(error.get("code") or "").strip().lower()
    return ""


def _should_fallback_to_file_upload(response, data):
    status_code = getattr(response, "status_code", None)
    error_code = _extract_error_code(data)
    error_message = _extract_error_message(data).lower()
    if status_code != 403:
        return False
    if error_code == "url_ownership_unverified":
        return True
    return "ownership" in error_message and "pull_from_url" in error_message


def _build_file_upload_source_info(video_size):
    if video_size <= 0:
        raise ValueError("Video size must be greater than zero")

    if video_size < CHUNK_SIZE_MIN:
        chunk_size = video_size
        total_chunk_count = 1
    else:
        chunk_size = min(CHUNK_SIZE_DEFAULT, video_size, CHUNK_SIZE_MAX)
        if chunk_size < CHUNK_SIZE_MIN:
            chunk_size = CHUNK_SIZE_MIN
        total_chunk_count = video_size // chunk_size
        if total_chunk_count < 1:
            total_chunk_count = 1

    return {
        "source": "FILE_UPLOAD",
        "video_size": int(video_size),
        "chunk_size": int(chunk_size),
        "total_chunk_count": int(total_chunk_count),
    }


def _download_video_to_tempfile(video_url):
    response = requests.get(video_url, stream=True, timeout=60)
    try:
        response.raise_for_status()
    except Exception:
        raise ValueError(f"Failed to download video for TikTok upload from URL: {video_url}")

    content_type = (response.headers.get("Content-Type") or "").split(";")[0].strip().lower()
    guessed_mime, _ = mimetypes.guess_type(video_url)
    mime_type = content_type or guessed_mime or "video/mp4"

    suffix = mimetypes.guess_extension(mime_type) or ".mp4"
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    total_size = 0
    try:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if not chunk:
                continue
            temp_file.write(chunk)
            total_size += len(chunk)
    finally:
        temp_file.flush()
        temp_file.close()
        response.close()

    if total_size <= 0:
        try:
            os.unlink(temp_file.name)
        except OSError:
            pass
        raise ValueError("Downloaded TikTok video is empty")

    return temp_file.name, total_size, mime_type


def _initialize_tiktok_file_upload(access_token, post_info, publish, video_size):
    payload = {
        "post_info": post_info,
        "source_info": _build_file_upload_source_info(video_size),
    }
    endpoint = (
        "/v2/post/publish/video/init/"
        if publish
        else "/v2/post/publish/inbox/video/init/"
    )
    response, data = _tiktok_request(
        "POST",
        endpoint,
        access_token,
        json=payload,
    )
    if not _is_success_response(response, data):
        raise ValueError(f"TikTok FILE_UPLOAD init failed ({response.status_code}: {_extract_error_message(data)})")

    publish_id = _extract_publish_id(data)
    upload_url = (data.get("data") or {}).get("upload_url")
    if not publish_id:
        raise ValueError("TikTok FILE_UPLOAD init did not return publish_id")
    if not upload_url:
        raise ValueError("TikTok FILE_UPLOAD init did not return upload_url")
    return str(publish_id), upload_url


def _upload_file_to_tiktok(upload_url, local_file_path, video_size, mime_type):
    if video_size <= 0:
        raise ValueError("Invalid TikTok video size")

    if video_size < CHUNK_SIZE_MIN:
        chunk_size = video_size
        total_chunk_count = 1
    else:
        chunk_size = min(CHUNK_SIZE_DEFAULT, video_size, CHUNK_SIZE_MAX)
        if chunk_size < CHUNK_SIZE_MIN:
            chunk_size = CHUNK_SIZE_MIN
        total_chunk_count = max(1, video_size // chunk_size)

    with open(local_file_path, "rb") as f:
        for index in range(total_chunk_count):
            start = index * chunk_size
            if index == total_chunk_count - 1:
                end = video_size - 1
            else:
                end = min(start + chunk_size - 1, video_size - 1)
            length = (end - start) + 1
            body = f.read(length)
            if len(body) != length:
                raise ValueError("Failed to read local video chunk for TikTok upload")

            response = requests.put(
                upload_url,
                data=body,
                headers={
                    "Content-Type": mime_type or "video/mp4",
                    "Content-Length": str(length),
                    "Content-Range": f"bytes {start}-{end}/{video_size}",
                },
                timeout=120,
            )
            expected_status = 201 if index == total_chunk_count - 1 else 206
            if response.status_code != expected_status:
                raise ValueError(
                    f"TikTok FILE_UPLOAD chunk upload failed ({response.status_code}) at chunk {index + 1}/{total_chunk_count}"
                )


def _publish_via_file_upload(access_token, post_info, publish, video_url):
    temp_path, video_size, mime_type = _download_video_to_tempfile(video_url)
    try:
        publish_id, upload_url = _initialize_tiktok_file_upload(
            access_token=access_token,
            post_info=post_info,
            publish=publish,
            video_size=video_size,
        )
        _upload_file_to_tiktok(
            upload_url=upload_url,
            local_file_path=temp_path,
            video_size=video_size,
            mime_type=mime_type,
        )
    finally:
        try:
            os.unlink(temp_path)
        except OSError:
            pass

    return {
        "publish_id": publish_id,
        "status": "published" if publish else "draft",
        "raw": {"source": "FILE_UPLOAD"},
    }


def get_tiktok_creator_info(access_token):
    response, data = _tiktok_request(
        "POST",
        "/v2/post/publish/creator_info/query/",
        access_token,
        json={},
    )
    if not _is_success_response(response, data):
        return {}
    return data.get("data") or {}


def create_tiktok_post(access_token, caption, media_urls, publish=False):
    if not access_token:
        raise ValueError("TikTok access token is missing")

    video_url = _extract_video_url(media_urls)
    if not video_url:
        raise ValueError("TikTok publish currently supports video media (.mp4/.mov/.avi/.mkv/.webm)")

    creator_info = get_tiktok_creator_info(access_token)
    privacy_options = creator_info.get("privacy_level_options") or []
    privacy_level = privacy_options[0] if privacy_options else "SELF_ONLY"

    post_info = {
        "title": (caption or "Posted via Frontliner").strip()[:2200],
        "privacy_level": privacy_level,
        "disable_duet": False,
        "disable_stitch": False,
        "disable_comment": False,
    }
    if creator_info.get("comment_disabled"):
        post_info["disable_comment"] = True
    if creator_info.get("duet_disabled"):
        post_info["disable_duet"] = True
    if creator_info.get("stitch_disabled"):
        post_info["disable_stitch"] = True

    payload = {
        "post_info": post_info,
        "source_info": {
            "source": "PULL_FROM_URL",
            "video_url": video_url,
        },
    }

    primary_endpoint = (
        "/v2/post/publish/video/init/"
        if publish
        else "/v2/post/publish/inbox/video/init/"
    )
    fallback_endpoint = (
        "/v2/post/publish/inbox/video/init/"
        if publish
        else "/v2/post/publish/video/init/"
    )

    last_error = None
    for endpoint in (primary_endpoint, fallback_endpoint):
        response, data = _tiktok_request(
            "POST",
            endpoint,
            access_token,
            json=payload,
        )
        if _is_success_response(response, data):
            publish_id = _extract_publish_id(data)
            if not publish_id:
                raise ValueError("TikTok publish ID missing in response")
            return {
                "publish_id": str(publish_id),
                "status": "published" if publish else "draft",
                "raw": data.get("data") or {},
            }

        if _should_fallback_to_file_upload(response, data):
            return _publish_via_file_upload(
                access_token=access_token,
                post_info=post_info,
                publish=publish,
                video_url=video_url,
            )
        last_error = f"{response.status_code}: {_extract_error_message(data)}"

    raise ValueError(f"TikTok publish init failed ({last_error})")


def get_tiktok_post_details(access_token, publish_id):
    if not access_token:
        return {"error": "TikTok access token is missing"}
    if not publish_id:
        return {"error": "TikTok publish_id is missing"}

    response, data = _tiktok_request(
        "POST",
        "/v2/post/publish/status/fetch/",
        access_token,
        json={"publish_id": str(publish_id)},
    )
    if not _is_success_response(response, data):
        return {
            "error": _extract_error_message(data),
            "status_code": response.status_code,
        }
    return data.get("data") or {}
