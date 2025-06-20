import os
import requests
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# ─────────── configuration ───────────
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")
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

# ─────────── helpers ───────────
def check_match_status():
    url = "https://bossopen.com/en/home"
    try:
        response = _get(url, "BossOpenMatchStatus")
        if response:
            # Example logic to parse the response and determine the match status
            # This is a placeholder and should be replaced with actual logic based on the response structure
            match_info = response.get('match_info', {})
            if match_info.get('status') == 'completed':
                winner = match_info.get('winner')
                if winner == 'Alex Michelsen':
                    return "p2"
                elif winner == 'Justin Engel':
                    return "p1"
            elif match_info.get('status') in ['canceled', 'postponed']:
                return "p3"
    except Exception as e:
        log.error(f"Error fetching match status: {str(e)}")
    return "p3"

# ─────────── main ───────────
if __name__ == "__main__":
    recommendation = check_match_status()
    print("recommendation:", recommendation)