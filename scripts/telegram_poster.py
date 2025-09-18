# scripts/telegram_poster.py
import os
import requests
from dotenv import load_dotenv

try:
    from utilities.logger import get_logger
    log = get_logger("telegram_poster")
except Exception:
    import logging
    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger("telegram_poster")

load_dotenv(".env.local")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL = os.getenv("TELEGRAM_CHANNEL")
BASE = f"https://api.telegram.org/bot{TOKEN}"
TIMEOUT = 60

def _ensure_env():
    if not TOKEN or not CHANNEL:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHANNEL")

def _is_url(path: str) -> bool:
    return path.startswith("http://") or path.startswith("https://")

def _send_photo(path_or_url: str, caption: str | None = None, reply_to: int | None = None) -> dict:
    """Works with either a local file path or a public URL."""
    _ensure_env()
    url = f"{BASE}/sendPhoto"
    data = {"chat_id": CHANNEL, "allow_sending_without_reply": True}
    if caption:
        data["caption"] = caption
    if reply_to:
        data["reply_to_message_id"] = reply_to

    if _is_url(path_or_url):
        # send URL directly
        data["photo"] = path_or_url
        r = requests.post(url, data=data, timeout=TIMEOUT)
    else:
        # send local file
        with open(path_or_url, "rb") as f:
            files = {"photo": f}
            r = requests.post(url, data=data, files=files, timeout=TIMEOUT)

    if r.status_code >= 400:
        raise RuntimeError(f"Telegram sendPhoto failed: {r.status_code} {r.text}")
    return r.json()["result"]

def post_campaign(metadata: dict, media: list[str]) -> dict:
    """
    metadata: legacy dict (title_en/title_hi/description_hi/price/hashtags/cta_whatsapp)
    media: list of file paths OR public URLs; first item is the head.
    """
    _ensure_env()
    title_hi = metadata.get("title_hi") or ""
    title_en = metadata.get("title_en") or ""
    desc_hi  = metadata.get("description_hi") or ""
    price    = metadata.get("price") or {}
    low, high, cur = price.get("low"), price.get("high"), price.get("currency", "INR")
    tags = " ".join(metadata.get("hashtags", []))
    cta  = metadata.get("cta_whatsapp") or ""

    price_line = f"₹{low}–₹{high} {cur}" if (low is not None and high is not None) else ""
    caption = "\n".join([s for s in [
        f"{title_hi} · {title_en}".strip(" ·"),
        price_line,
        desc_hi,
        "",
        tags if tags else None,
        "",
        f"Buy: {cta}" if cta else None
    ] if s is not None and s != ""])

    head = media[0]
    log.info(f"[प्रchar] Telegram head: {head}")
    head_msg = _send_photo(head, caption=caption)
    thread_id = head_msg["message_id"]

    for m in media[1:]:
        log.info(f"Reply media: {m}")
        _send_photo(m, reply_to=thread_id)

    result = {"platform": "telegram", "thread_head_id": thread_id, "count": len(media)}
    log.info(f"[प्रchar] Telegram publish complete: {result}")
    return result
