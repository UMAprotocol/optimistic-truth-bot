import os
import requests
import logging
from datetime import datetime
from dotenv import load_dotenv

# ─────────── configuration ───────────
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")
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
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
        except requests.exceptions.RequestException as e:
            log.error(f"Request failed: {e}")
            continue
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
def get_game_result(date_str):
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date_str}"
    games = _get(url, "GamesByDate")
    if games is None:
        return "p4"  # Unable to fetch data
    for game in games:
        if game['HomeTeam'] == 'NYK' and game['AwayTeam'] == 'IND':
            if game['Status'] == 'Final':
                if game['HomeTeamScore'] > game['AwayTeamScore']:
                    return "p2"  # Knicks win
                else:
                    return "p1"  # Pacers win
            elif game['Status'] == 'Postponed':
                return "p4"  # Game postponed
            elif game['Status'] == 'Canceled':
                return "p3"  # Game canceled
    return "p4"  # No matching game found or in progress

# ─────────── main ───────────
if __name__ == "__main__":
    DATE = "2025-05-25"
    print("recommendation:", get_game_result(DATE))