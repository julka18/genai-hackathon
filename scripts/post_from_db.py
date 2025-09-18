import argparse
import sys
from utilities.logger import get_logger, step
from db.firestore_loader import fetch_product_by_slug, to_telegram_payload
from scripts.telegram_poster import post_campaign

log = get_logger("post_from_db")

def main():
    p = argparse.ArgumentParser(description="प्रchar | Post product from Firestore to Telegram")
    p.add_argument("--slug", required=True, help="Product slug in Firestore (e.g., kalamkari-scarf)")
    args = p.parse_args()

    try:
        product = fetch_product_by_slug(args.slug)
    except Exception as e:
        log.error("Fetch failed: %s", e)
        sys.exit(1)

    meta, media_urls = to_telegram_payload(product)
    log.info("Product '%s' → %d image(s)", args.slug, len(media_urls))

    with step("Post campaign", items=len(media_urls)):
        res = post_campaign(meta, media_urls)

    log.info("Posted: %s", res)
    print(res)

if __name__ == "__main__":
    main()
