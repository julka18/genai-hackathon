# प्रchar — Team Guide (Phase 0)

> AI-assisted marketplace helper for Indian artisans.  
> **Phase-0** includes a premium “liquid-glass” login page (Firebase Phone Auth) and a Telegram publisher demo that posts a campaign (media + caption) to our shared channel.

**Join our Telegram channel:** https://t.me/prachar_artisans

---

## 0) TL;DR (5 commands)

```bash
git clone <repo-url> && cd genai-hackathon

# create local secrets
printf "TELEGRAM_BOT_TOKEN=<ask-maintainer>\nTELEGRAM_CHANNEL=@prachar_artisans\n" > .env.local

# install deps with uv (https://astral.sh/uv)
uv sync

# run the Telegram demo
uv run python scripts/test_campaign.py
```

You should see posts in **@prachar_artisans** and a new log file under `logs/`.

---

## 1) Repo Architecture

```
genai-hackathon/
├─ campaigns/                    # campaign assets/samples you (devs) add here
│  └─ EXAMPLE/
│     └─ assets/
│        ├─ img1.jpg
│        └─ img2.jpg
│
├─ scripts/                      # Python utilities & demos
│  ├─ __init__.py
│  ├─ telegram_poster.py         # posts a campaign to Telegram (head + replies)
│  └─ test_campaign.py           # demo runner (edit metadata/media paths here)
│
├─ utilities/                    # shared helper modules
│  ├─ __init__.py
│  └─ logger.py                  # step-based logger; writes to logs/<timestamp>.log
│
├─ web/                          # static web (Phase 0)
│  └─ auth/
│     ├─ index.html              # login page (liquid-glass UI)
│     ├─ style.css               # aesthetic system + glass effect
│     └─ app.js                  # Firebase config + phone OTP flow
│
├─ logs/                         # generated at runtime (gitignored)
├─ .env.local                    # local secrets (NOT committed)
├─ pyproject.toml                # Python project + dependencies (managed by uv)
└─ README.md
```

**Data flow (Phase 0):**

```mermaid
flowchart LR
  A(Media files) --> B(Telegram Poster Script)
  B -->|Bot API| C(@prachar_artisans Channel)
  B --> D(Logs/*.log)
```

---

## 2) Prerequisites

- **Python 3.10+** (check: `python3 --version`)
- **uv** (blazing-fast Python package manager)

Install uv (macOS/Linux):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# restart terminal
uv --version
```

Windows: use PowerShell from the site above, or install via pipx.

*(Node is **not required** for the Telegram demo. The login page is plain HTML/CSS/JS.)*

---

## 3) Telegram Access (Channel + Bot)

1. **Join our channel:** https://t.me/prachar_artisans  
2. Ensure the bot is **Admin** in the channel with **Post messages** permission. (Ask in team chat; already configured most likely.)
3. *(Optional but helpful)* DM the bot once and tap **Start** to allow direct sanity checks to your DM.

---

## 4) Local Environment (`.env.local`)

Create a file named **`.env.local`** at the repo root:

```
TELEGRAM_BOT_TOKEN=xxxxxxxx:yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy
TELEGRAM_CHANNEL=@prachar_artisans
```

> Ask the maintainer for the current token.  
> **Never commit** `.env.local`.

---

## 5) Install Dependencies

```bash
uv sync
```

- Reads `pyproject.toml` and installs packages (e.g., `requests`, `python-dotenv`).
- Creates/updates a local virtual environment under `.venv` (handled by uv).

---

## 6) Run the Telegram Publisher Demo

This demo posts a small campaign to the channel:

```bash
uv run python scripts/test_campaign.py
```

**What happens**
- The **first media** is posted with a bilingual caption (head post).
- Remaining media are posted as **replies** under the head (threaded).
- Detailed step logs are written to `logs/YYYYMMDD_HHMMSS.log`.

**Customize the campaign**
- Open `scripts/test_campaign.py`.
- Edit `metadata` (titles, description, hashtags, CTA link).
- Update `media` with your own paths, e.g.:

```python
media = [
  "campaigns/<yourname>/assets/photo1.jpg",
  "campaigns/<yourname>/assets/reel1.mp4",
]
```

Re-run the command to post your variant.

---

## 7) Run the Login Page (Optional UX Check)

The Phase-0 login page uses Firebase Phone Auth (OTP). Serve it locally:

```bash
python3 -m http.server 5173
# open in browser:
# http://localhost:5173/web/auth/index.html
```

**Firebase notes**
- Enable **Phone** sign-in in Firebase → Authentication → Sign-in method.
- Add **localhost** and **127.0.0.1** to **Authorized domains**.
- `web/auth/app.js` expects your Firebase web config (paste your config object).

---

## 8) Logs & Diagnostics

- All important steps are logged via `utilities/logger.py` to **`logs/`**:
  - START/DONE/FAIL for head post, replies, and API calls.
  - Telegram JSON responses for traceability.

Inspect logs:
```bash
tail -f logs/*.log
```

---

## 9) Troubleshooting

**`ModuleNotFoundError: 'utilities'`**  
- Run from repo root using module mode:  
  ```bash
  uv run python -m scripts.test_campaign
  ```
- Ensure `utilities/__init__.py` exists.

**`Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHANNEL`**  
- Check `.env.local` exists and has:
  ```
  TELEGRAM_BOT_TOKEN=...
  TELEGRAM_CHANNEL=@prachar_artisans
  ```
- No quotes, no trailing spaces.

**`Bad Request: chat not found`**  
- The bot is not an Admin in the channel or the channel handle is wrong.

**502/504 (Bad Gateway/Gateway Timeout)**  
- Temporary Telegram API hiccup → re-run after a minute; try without VPN/proxy.

**Nothing appears in `logs/`**  
- Ensure `utilities/logger.py` exists and that your script imports it (`from utilities.logger import get_logger, step`).
- Re-run from repo root.

---

## 10) Team Workflow (Phase 0)

```bash
git pull origin main

# create your sample campaign
mkdir -p campaigns/<yourname>/assets
# drop media files (jpg/png/mp4/webm)

# point test_campaign.py to your media and metadata
uv run python scripts/test_campaign.py
# verify posts in channel + logs generated

git add .
git commit -m "feat(campaign): post <yourname> sample; docs/logs updated"
git push origin main
```

**Commit style (suggested):**
- `feat(logging): ...` for logging or tooling improvements
- `docs(readme): ...` for docs
- `feat(publisher): ...` when adding surfaces or features

---

## Roadmap (next)

- **Phase 1**: Wire Gemini-generated creatives (images/reels/captions) into this publisher.  
- Publish to more free surfaces (Reddit, X/Twitter, etc.) via simple adapters.  
- Wrap the poster into a **LangFlow / LangServe** endpoint for “publish everywhere” with one call.  
- Add minimal DB for campaign state & artisan profiles.

---

If you get stuck, paste your command + error in the team chat—we’ll fix it fast. ✌️
