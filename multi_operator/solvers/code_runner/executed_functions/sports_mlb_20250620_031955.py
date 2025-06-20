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
def check_player_performance(player_id, game_id):
    url = f"https://api.sportsdata.io/v3/nba/stats/json/PlayerGameStatsByPlayer/{game_id}/{player_id}"
    game_stats = _get(url, "PlayerGameStatsByPlayer")
    if game_stats:
        points = game_stats.get("Points", 0)
        return points
    return None

def find_game_and_player(date_str, team_name, opponent_name, player_name):
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date_str}"
    games = _get(url, "GamesByDate")
    if games:
        for game in games:
            if (game["HomeTeam"] == team_name or game["AwayTeam"] == team_name) and \
               (game["HomeTeam"] == opponent_name or game["AwayTeam"] == opponent_name):
                player_url = f"https://api.sportsdata.io/v3/nba/scores/json/Players/{team_name}"
                players = _get(player_url, "Players")
                for player in players:
                    if player["FirstName"] + " " + player["LastName"] == player_name:
                        return game["GameID"], player["PlayerID"]
    return None, None

# ─────────── main ───────────
if __name__ == "__main__":
    DATE = "2025-06-19"
    TEAM_NAME = "Indiana Pacers"
    OPPONENT_NAME = "Oklahoma City Thunder"
    PLAYER_NAME = "Pascal Siakam"

    game_id, player_id = find_game_and_player(DATE, TEAM_NAME, OPPONENT_NAME, PLAYER_NAME)
    if game_id and player_id:
        points = check_player_performance(player_id, game_id)
        if points is not None:
            if points >= 23:
                print("recommendation: p2")  # Yes, scored 23+ points
            else:
                print("recommendation: p1")  # No, did not score 23+ points
        else:
            print("recommendation: p1")  # No data found, assume no play or below threshold
    else:
        print("recommendation: p1")  # No game or player found, assume no play