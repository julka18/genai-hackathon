# scripts/test_campaign.py
from utilities.logger import get_logger, step
from scripts.telegram_poster import post_campaign

log = get_logger("test_campaign")

metadata = {
    "title_en": "Handmade Kalamkari Scarf",
    "title_hi": "हैंडमेड कलमकारी स्कार्फ",
    "description_hi": "प्राकृतिक रंग, हैंड-ब्लॉक प्रिंट",
    "price": {"low": 799, "high": 1199, "currency": "INR"},
    "hashtags": ["#kalamkari", "#handmade", "#artisan", "#india"],
    "cta_whatsapp": "https://wa.me/91XXXXXXXXXX?text=Kalamkari%20Scarf",
}
media = [
    "campaigns/EXAMPLE/assets/img1.jpg",
    "campaigns/EXAMPLE/assets/img2.jpg",
]

with step("Post campaign", items=len(media)):
    res = post_campaign(metadata, media)
log.info("Posted: %s", res)
