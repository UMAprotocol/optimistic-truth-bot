import os
import requests
from dotenv import load_dotenv
import logging

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
def check_player_performance(player_name, game_date):
    url = f"https://api.sportsdata.io/v3/nba/stats/json/PlayerGameStatsByDate/{game_date}"
    games = _get(url, "PlayerGameStatsByDate")
    if games:
        for game in games:
            if game['Name'] == player_name:
                points = game.get('Points', 0)
                return points
    return None

# ─────────── main ───────────
if __name__ == "__main__":
    GAME_DATE = "2025-05-31"
    PLAYER_NAME = "Jalen Brunson"
    points = check_player_performance(PLAYER_NAME, GAME_DATE)
    if points is None:
        print("recommendation: p1")  # No data or player did not play
    elif points > 31.5:
        print("recommendation: p2")  # Yes, scored more than 31.5 points
    else:
        print("recommendation: p1")  # No, did not score more than 31.5 points