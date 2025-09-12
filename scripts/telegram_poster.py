import os
import time
import json
import requests
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from utilities.logger import get_logger, step   # 👈 using your logger

log = get_logger("telegram_poster")

# ---------- Load secrets ----------
dotenv_path = find_dotenv(filename=".env.local", usecwd=True)
if dotenv_path:
    load_dotenv(dotenv_path, override=True)
    log.info("Loaded .env.local → %s", dotenv_path)
else:
    log.warning(".env.local not found; relying on system env")

TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL = os.getenv("TELEGRAM_CHANNEL")

if not TOKEN or not CHANNEL:
    raise RuntimeError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHANNEL")

API_BASE = f"https://api.telegram.org/bot{TOKEN}"

IMG_EXT = (".jpg", ".jpeg", ".png", ".webp")
VID_EXT = (".mp4", ".mov", ".webm")


def is_img(path: str) -> bool:
    return path.lower().endswith(IMG_EXT)


def is_vid(path: str) -> bool:
    return path.lower().endswith(VID_EXT)


def send_media(path: str, caption: str | None = None, reply_to: int | None = None) -> int:
    """Send a photo or video to the Telegram channel. Returns message_id."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")

    endpoint = None
    files = None
    if is_img(str(p)):
        endpoint = f"{API_BASE}/sendPhoto"
        files = {"photo": open(p, "rb")}
    elif is_vid(str(p)):
        endpoint = f"{API_BASE}/sendVideo"
        files = {"video": open(p, "rb")}
    else:
        raise ValueError(f"Unsupported media type: {p.suffix}")

    data = {"chat_id": CHANNEL, "caption": caption, "reply_to_message_id": reply_to}

    with step("Send media", file=str(p), reply_to=reply_to):
        r = requests.post(endpoint, data=data, files=files, timeout=120)
        r.raise_for_status()
        resp = r.json()
        log.info("Telegram response: %s", json.dumps(resp, ensure_ascii=False))

        if not resp.get("ok"):
            raise RuntimeError(f"Telegram API error: {resp}")

        mid = int(resp["result"]["message_id"])
        log.info("Message_id=%s", mid)
        return mid


def post_campaign(metadata: dict, media_paths: list[str]) -> dict:
    """Posts a campaign pack: first media with caption, others as replies."""
    price = metadata["price"]
    caption = (
        f"{metadata['title_hi']} • {metadata['title_en']}\n"
        f"₹{price['low']}–₹{price['high']} {price.get('currency','INR')}\n"
        f"{metadata.get('description_hi','')}\n\n"
        f"{' '.join(metadata.get('hashtags', []))}\n\n"
        f"Buy: {metadata['cta_whatsapp']}"
    ).strip()

    log.info("Channel: %s", CHANNEL)
    log.info("Media count: %d", len(media_paths))

    with step("Head post", file=media_paths[0]):
        head_id = send_media(media_paths[0], caption=caption)
    message_ids = [head_id]

    with step("Thread remaining media", count=max(0, len(media_paths) - 1)):
        for p in media_paths[1:]:
            time.sleep(0.6)
            message_ids.append(send_media(p, caption=None, reply_to=head_id))

    result = {"ok": True, "channel": CHANNEL, "message_ids": message_ids}
    log.info("✅ Campaign posted: %s", result)
    return result
