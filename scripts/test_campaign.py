# scripts/test_campaign.py
"""
Run a campaign from a folder where:
  campaigns/<slug>/
    ├─ assets/           # media files (posting order = list in metadata.assets or filename sort)
    └─ metadata.json     # single source of truth (titles/description/price/hashtags/cta/assets/head_index)

Usage:
  uv run python scripts/test_campaign.py --campaign campaigns/kalamkari-scarf
"""
import argparse
import json
import sys
from pathlib import Path
from typing import List

from utilities.logger import get_logger, step
from scripts.telegram_poster import post_campaign  # expects (metadata: dict, media: List[str])

# NOTE: current telegram_poster typically supports IMAGES via sendPhoto.
# If you have videos in assets, they will be skipped here to avoid API errors.
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

log = get_logger("test_campaign")


def load_metadata(campaign_dir: Path) -> dict:
    meta_path = campaign_dir / "metadata.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"metadata.json not found at {meta_path}")
    with open(meta_path, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_media(campaign_dir: Path, meta: dict) -> List[Path]:
    """Prefer explicit list in metadata['assets']; else scan assets/ and pick images."""
    assets_dir = campaign_dir / "assets"
    if not assets_dir.exists():
        raise FileNotFoundError(f"assets folder not found at {assets_dir}")

    # Build candidate list
    if isinstance(meta.get("assets"), list) and meta["assets"]:
        candidates = [(campaign_dir / rel).resolve() for rel in meta["assets"]]
    else:
        candidates = sorted(assets_dir.iterdir(), key=lambda p: p.name.lower())

    media_paths: List[Path] = []
    skipped: List[str] = []
    for p in candidates:
        if not p.exists():
            skipped.append(f"missing: {p}")
            continue
        if p.suffix.lower() not in IMAGE_EXT:
            skipped.append(f"unsupported (not image): {p.name}")
            continue
        media_paths.append(p)

    if skipped:
        for s in skipped:
            log.warning("Asset skipped: %s", s)

    if not media_paths:
        raise FileNotFoundError(f"No usable image media found in {assets_dir}")

    # Optional head_index
    head_index = meta.get("head_index")
    if isinstance(head_index, int) and 0 <= head_index < len(media_paths):
        head = media_paths.pop(head_index)
        media_paths.insert(0, head)

    return media_paths


def to_legacy_metadata(meta: dict) -> dict:
    """
    Map standardized metadata.json to the legacy shape expected by post_campaign():
      - title_en, title_hi, description_hi, price, hashtags, cta_whatsapp
    """
    titles = meta.get("titles", {})
    desc = meta.get("description", {})
    return {
        "title_en": titles.get("en") or meta.get("title_en"),
        "title_hi": titles.get("hi") or meta.get("title_hi"),
        "description_hi": desc.get("hi") or meta.get("description_hi"),
        "price": meta.get("price", {}),
        "hashtags": meta.get("hashtags", []),
        "cta_whatsapp": (meta.get("cta") or {}).get("whatsapp") or meta.get("cta_whatsapp"),
    }


def main():
    parser = argparse.ArgumentParser(description="प्रchar | Test campaign poster (Telegram)")
    parser.add_argument(
        "--campaign",
        default="campaigns/kalamkari-scarf",
        help="Path to the campaign folder (e.g., campaigns/kalamkari-scarf)",
    )
    args = parser.parse_args()

    campaign_dir = Path(args.campaign).resolve()
    if not campaign_dir.exists():
        log.error("Campaign folder not found: %s", campaign_dir)
        sys.exit(1)

    meta = load_metadata(campaign_dir)
    media_paths = resolve_media(campaign_dir, meta)
    legacy_meta = to_legacy_metadata(meta)

    media_strs = [str(p) for p in media_paths]
    log.info("Campaign: %s", campaign_dir.name)
    log.info("Media count (images): %d", len(media_strs))
    log.info("Head media: %s", Path(media_strs[0]).name)

    with step("Post campaign", items=len(media_strs)):
        res = post_campaign(legacy_meta, media_strs)

    log.info("Posted: %s", res)
    print(res)


if __name__ == "__main__":
    main()
