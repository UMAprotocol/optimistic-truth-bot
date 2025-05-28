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
log = logging.getLogger(__name__)

# ─────────── generic GET wrapper ───────────
def _get(url, tag, retries=3, backoff=1.5):
    for i in range(retries):
        log.debug(f"[{tag}] → {url}")
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            log.debug(f"[{tag}] ← {r.status_code} {r.reason}")
            if r.ok:
                log.debug(f"[{tag}] payload length: {len(r.json())}")
                return r.json()
            if r.status_code in (401, 403):
                log.error(f"[{tag}] blocked — not in plan")
                return None
            if r.status_code == 404:
                log.warning(f"[{tag}] 404 — not found")
                return []
            if r.status_code == 429:
                wait = backoff * 2**i
                log.warning(f"[{tag}] 429 — back-off {wait:.1f}s")
                time.sleep(wait)
                continue
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            log.error(f"Request failed: {e}")
    return None

# ─────────── helpers ───────────
def check_game_and_performance(date_str):
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date_str}"
    games = _get(url, "GamesByDate")
    if games:
        for game in games:
            if game['HomeTeam'] == 'MIN' or game['AwayTeam'] == 'MIN':
                if game['Status'] == 'Final':
                    game_id = game['GameID']
                    stats_url = f"https://api.sportsdata.io/v3/nba/stats/json/PlayerGameStatsByGame/{game_id}"
                    stats = _get(stats_url, "PlayerGameStatsByGame")
                    if stats:
                        for stat in stats:
                            if stat['PlayerID'] == 20002571:  # Assuming this is Anthony Edwards' PlayerID
                                points = stat['Points']
                                if points > 30.5 and game['Winner'] == 'MIN':
                                    return "p2"  # Yes
                                else:
                                    return "p1"  # No
    return "p1"  # No, default if no data found or conditions not met

# ─────────── main ───────────
if __name__ == "__main__":
    DATE = "2025-05-26"
    recommendation = check_game_and_performance(DATE)
    print("recommendation:", recommendation)