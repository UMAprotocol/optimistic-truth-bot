import os
import requests
import logging
from datetime import datetime
from dotenv import load_dotenv

# ─────────── configuration ───────────
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_CBB_API_KEY")
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()])
logging.getLogger().addFilter(
    lambda r: setattr(r, "msg",
        re.sub(re.escape(API_KEY), "******", r.getMessage())) or True)
log = logging.getLogger(__name__)

# ─────────── generic GET wrapper ───────────
def _get(url, tag, retries=3, backoff=1.5):
    for i in range(retries):
        log.debug(f"[{tag}] → {url}")
        r = requests.get(url, headers=HEADERS, timeout=10)
        log.debug(f"[{tag}] ← {r.status_code} {r.reason}")
        if r.ok:
            log.debug(f"[{tag}] payload length: {len(r.json())}")
            return r.json()
        if r.status_code in (401, 403):
            log.error(f"[{tag}] blocked — not in plan"); return None
        if r.status_code == 404:
            log.warning(f"[{tag}] 404 — not found"); return []
        if r.status_code == 429:
            wait = backoff * 2**i
            log.warning(f"[{tag}] 429 — back-off {wait:.1f}s")
            time.sleep(wait); continue
        r.raise_for_status()
    return None

# ─────────── main ───────────
if __name__ == "__main__":
    EVENT_DATE = "2025-05-24"
    TERM = "Beast"
    URL = "https://api.sportsdata.io/v3/cbb/scores/json/PlayerSeasonStats/2025"

    # Fetch data from the API
    data = _get(URL, "PlayerSeasonStats")
    if data is None:
        print("recommendation: p1")  # No data available, resolve to "No"
    else:
        # Check if the term is mentioned in the data
        mentioned = any(TERM.lower() in player.get('Name', '').lower() for player in data)
        if mentioned:
            print("recommendation: p2")  # Term is mentioned, resolve to "Yes"
        else:
            print("recommendation: p1")  # Term is not mentioned, resolve to "No"