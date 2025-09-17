from __future__ import annotations
import os
from typing import Tuple, List, Dict

from google.cloud import firestore
from google.oauth2 import service_account
from dotenv import load_dotenv

# Reads FIREBASE_PROJECT_ID, GOOGLE_APPLICATION_CREDENTIALS, FIREBASE_COLLECTION_PRODUCTS
def _client() -> firestore.Client:
    load_dotenv(".env.local")
    project_id = os.getenv("FIREBASE_PROJECT_ID")
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not project_id or not cred_path:
        raise RuntimeError("Missing FIREBASE_PROJECT_ID or GOOGLE_APPLICATION_CREDENTIALS")
    creds = service_account.Credentials.from_service_account_file(cred_path)
    return firestore.Client(project=project_id, credentials=creds)

def fetch_product_by_slug(slug: str) -> Dict:
    col = os.getenv("FIREBASE_COLLECTION_PRODUCTS", "products")
    db = _client()
    qs = db.collection(col).where("slug", "==", slug).limit(1).stream()
    doc = next(qs, None)
    if not doc:
        raise LookupError(f"No product with slug={slug}")
    data = doc.to_dict() or {}
    data["id"] = doc.id
    return data

def to_telegram_payload(product: Dict) -> Tuple[Dict, List[str]]:
    """Map Firestore product to (metadata, media_urls) expected by post_campaign()."""
    titles = product.get("titles", {})
    desc   = product.get("description", {})
    price  = product.get("price", {}) or {}
    tags   = product.get("hashtags", []) or []
    cta    = (product.get("cta") or {}).get("whatsapp")

    # legacy metadata shape
    meta = {
        "title_en": titles.get("en"),
        "title_hi": titles.get("hi"),
        "description_hi": desc.get("hi"),
        "price": price,
        "hashtags": tags,
        "cta_whatsapp": cta,
    }

    media = product.get("media", []) or []
    # order by 'order' (default 0); only images with url
    media_urls = [
        m["url"] for m in sorted(media, key=lambda x: x.get("order", 0))
        if isinstance(m, dict) and m.get("type") == "image" and m.get("url")
    ]
    if not media_urls:
        raise ValueError("No usable image URLs in product.media")

    return meta, media_urls
