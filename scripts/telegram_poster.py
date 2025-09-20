# scripts/telegram_poster.py
"""
Telegram campaign poster for प्रchar
Now supports base64 images directly (no Cloudinary / local files).
"""

import os
import base64
import requests
from io import BytesIO
from dotenv import load_dotenv
from utilities.logger import get_logger, step

# load env
load_dotenv(".env.local")

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL = os.getenv("TELEGRAM_CHANNEL")

log = get_logger("telegram_poster")

API_URL = f"https://api.telegram.org/bot{TOKEN}"


def _decode_base64_image(data_url: str) -> BytesIO:
    """
    Convert a base64 data URL string into a BytesIO stream.
    Expects format like: data:image/jpeg;base64,/9j/4AAQSk...
    """
    if "," in data_url:
        _, encoded = data_url.split(",", 1)
    else:
        encoded = data_url
    img_bytes = base64.b64decode(encoded)
    return BytesIO(img_bytes)


def _send_photo(photo_stream: BytesIO, caption: str = None, reply_to: int = None):
    """
    Send a single photo to Telegram.
    """
    url = f"{API_URL}/sendPhoto"
    files = {"photo": photo_stream}
    data = {"chat_id": CHANNEL}
    if caption:
        data["caption"] = caption
        data["parse_mode"] = "HTML"
    if reply_to:
        data["reply_to_message_id"] = reply_to

    resp = requests.post(url, data=data, files=files, timeout=30)
    if not resp.ok:
        raise Exception(f"Telegram sendPhoto failed: {resp.text}")
    return resp.json()["result"]["message_id"]


def post_campaign(metadata: dict, media_base64: list[str]):
    """
    Post campaign to Telegram.
    Args:
        metadata: dict with title/description/hashtags/cta
        media_base64: list of base64 strings (data URLs)

    Flow:
    - First image → main caption post
    - Remaining images → reply chain
    """
    if not TOKEN or not CHANNEL:
        raise RuntimeError("TELEGRAM_BOT_TOKEN or TELEGRAM_CHANNEL missing in .env.local")

    title_en = metadata.get("title_en", "")
    title_hi = metadata.get("title_hi", "")
    desc_hi = metadata.get("description_hi", "")
    price = metadata.get("price", {})
    hashtags = " ".join(metadata.get("hashtags", []))
    cta = metadata.get("cta_whatsapp", "")

    caption_parts = []
    if title_hi or title_en:
        caption_parts.append(f"<b>{title_hi} {title_en}</b>")
    if desc_hi:
        caption_parts.append(desc_hi)
    if price:
        low = price.get("low")
        high = price.get("high")
        cur = price.get("currency", "INR")
        if low and high:
            caption_parts.append(f"💰 {low}–{high} {cur}")
    if hashtags:
        caption_parts.append(hashtags)
    if cta:
        caption_parts.append(f"<a href='{cta}'>Order on WhatsApp</a>")

    caption = "\n".join(caption_parts)

    with step("Posting campaign to Telegram", items=len(media_base64)):
        thread_id = None
        for idx, b64 in enumerate(media_base64):
            try:
                photo_stream = _decode_base64_image(b64)
                if idx == 0:
                    # head post with caption
                    thread_id = _send_photo(photo_stream, caption=caption)
                    log.info("Head post sent (msg_id=%s)", thread_id)
                else:
                    # replies
                    _send_photo(photo_stream, reply_to=thread_id)
                    log.info("Reply image %s sent", idx + 1)
            except Exception as e:
                log.error("Error posting image %s: %s", idx + 1, e)

    return {"status": "ok", "thread_id": thread_id}
