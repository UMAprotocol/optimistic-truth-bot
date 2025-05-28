import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# ─────────── configuration ───────────
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# ─────────── generic GET wrapper ───────────
def _get(url, tag, retries=3, backoff=1.5):
    for i in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.ok:
                return response.json()
            if response.status_code in (401, 403, 404):
                return None
            if response.status_code == 429:
                time.sleep(backoff * 2**i)
        except requests.RequestException:
            continue
    return None

# ─────────── helpers ───────────
def get_player_stats_by_game(game_id, player_name):
    url = f"https://api.sportsdata.io/v3/nba/stats/json/PlayerGameStatsByPlayer/{game_id}/{player_name}"
    game_stats = _get(url, "PlayerGameStatsByPlayer")
    if game_stats:
        return game_stats.get("Points")
    return None

def find_game_id(date, team):
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date}"
    games = _get(url, "GamesByDate")
    if games:
        for game in games:
            if team in [game["HomeTeam"], game["AwayTeam"]]:
                return game["GameID"]
    return None

# ─────────── main ───────────
def main():
    DATE = "2025-05-27"
    TEAM = "New York Knicks"
    PLAYER_NAME = "Jalen Brunson"
    POINTS_THRESHOLD = 29.5

    game_id = find_game_id(DATE, TEAM)
    if not game_id:
        print("recommendation: p1")  # No game found, resolve to "No"
        return

    points = get_player_stats_by_game(game_id, PLAYER_NAME)
    if points is None:
        print("recommendation: p1")  # Player did not play or data unavailable, resolve to "No"
    elif points > POINTS_THRESHOLD:
        print("recommendation: p2")  # Yes, player scored more than 29.5 points
    else:
        print("recommendation: p1")  # No, player did not score more than 29.5 points

if __name__ == "__main__":
    main()