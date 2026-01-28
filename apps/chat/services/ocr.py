
import os
import base64
from typing import Optional, Dict, Any
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def _to_data_url(image_bytes: bytes, content_type: str) -> str:
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{content_type};base64,{b64}"

def run_ocr(image_bytes: bytes, content_type: str = "image/jpeg") -> str:
    """
    Extract all visible text (Bangla/English), including serial/model/barcode text if present.
    """
    data_url = _to_data_url(image_bytes, content_type)

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract ALL visible text from this image. Include Bangla/English. If there are barcodes/serial/model numbers, include them exactly."},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
    )

    return (resp.choices[0].message.content or "").strip()

def run_vision_caption(image_bytes: bytes, content_type: str = "image/jpeg") -> str:
    """
    Understand the image even if there is no text: identify product/object, brand/model guesses,
    key visible attributes, and anything helpful for 'is this available?' type queries.
    """
    data_url = _to_data_url(image_bytes, content_type)

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.2,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Describe what is in this image for product identification.\n"
                            "- What product/object is it?\n"
                            "- Brand/model if you can infer (say 'not sure' if uncertain)\n"
                            "- Key visible features (color, size, packaging, label, type)\n"
                            "- If multiple items, summarize them\n"
                            "Keep it concise but informative."
                        ),
                    },
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
    )

    return (resp.choices[0].message.content or "").strip()

def analyze_image(image_bytes: bytes, content_type: str = "image/jpeg") -> Dict[str, Any]:
    """
    Do both OCR + Vision caption. Returns dict.
    """
    ocr_text = ""
    caption = ""
    try:
        ocr_text = run_ocr(image_bytes, content_type=content_type)
    except Exception as e:
        ocr_text = f"[OCR_ERROR] {type(e).__name__}: {e}"

    try:
        caption = run_vision_caption(image_bytes, content_type=content_type)
    except Exception as e:
        caption = f"[VISION_ERROR] {type(e).__name__}: {e}"

    return {"ocr_text": ocr_text, "caption": caption, "content_type": content_type}
