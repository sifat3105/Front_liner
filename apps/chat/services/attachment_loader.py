# services/attachment_loader.py
from typing import List, Dict, Any
import requests

def download_images(attachments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

    images = []
    for att in attachments or []:
        if att.get("type") != "image":
            continue

        payload = att.get("payload") or {}
        url = payload.get("url")
        if not url:
            continue

        r = requests.get(url, timeout=15)
        r.raise_for_status()

        content_type = r.headers.get("content-type", "image/jpeg")
        # sometimes content-type includes charset etc
        content_type = content_type.split(";")[0].strip().lower() or "image/jpeg"

        images.append({"bytes": r.content, "content_type": content_type, "url": url})

    return images
