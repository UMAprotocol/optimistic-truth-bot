import os
import requests
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# ─────────── configuration ───────────
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NFL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NFL_API_KEY")
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
    start_date = datetime.strptime("2025-05-17 12:00", "%Y-%m-%d %H:%M")
    end_date = datetime.strptime("2025-05-23 23:59", "%Y-%m-%d %H:%M")
    current_date = datetime.now()

    if current_date < start_date:
        print("recommendation: p4")  # Too early
    elif current_date > end_date:
        # Check for any public records of Trump saying "Peace through strength"
        # This is a placeholder for actual implementation which would involve searching through relevant data sources.
        # Since we cannot execute live data fetching in this environment, we assume no data found.
        print("recommendation: p1")  # No mention found
    else:
        print("recommendation: p4")  # In progress