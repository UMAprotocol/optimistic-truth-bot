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
def check_game_and_player_performance(date_str):
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date_str}"
    games = _get(url, "GamesByDate")
    if games:
        for game in games:
            if game['HomeTeam'] == 'OKC' or game['AwayTeam'] == 'OKC':
                if game['Status'] != 'Final':
                    return "p4"  # Game not completed
                if game['Status'] in ['Canceled', 'Postponed']:
                    return "p1"  # Game canceled or postponed
                # Check game outcome and player performance
                winner = game['HomeTeam'] if game['HomeTeamScore'] > game['AwayTeamScore'] else game['AwayTeam']
                if winner != 'OKC':
                    return "p1"  # Thunder did not win
                # Check player performance
                player_stats_url = f"https://api.sportsdata.io/v3/nba/stats/json/PlayerGameStatsByDate/{date_str}"
                player_stats = _get(player_stats_url, "PlayerGameStatsByDate")
                for stat in player_stats:
                    if stat['PlayerID'] == 20002077 and stat['Points'] > 33.5:  # Assuming SGA's PlayerID is 20002077
                        return "p2"  # SGA scored more than 33.5 points and Thunder won
    return "p1"  # Default to Thunder not winning or SGA not scoring enough

# ─────────── main ───────────
if __name__ == "__main__":
    DATE = "2025-06-05"
    recommendation = check_game_and_player_performance(DATE)
    print("recommendation:", recommendation)