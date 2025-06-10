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
                continue
            response.raise_for_status()
        except requests.RequestException:
            if i < retries - 1:
                time.sleep(backoff * (2 ** i))
            else:
                raise

# ─────────── helpers ───────────
def fetch_player_stats_by_game(date, player_name):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/nba/stats/json/PlayerGameStatsByDate/{formatted_date}"
    games = _get(url, "PlayerGameStatsByDate")
    if games:
        for game in games:
            if game['Name'] == player_name:
                return game
    return None

# ─────────── main ───────────
if __name__ == "__main__":
    game_date = "2025-05-28"
    player_name = "Anthony Edwards"
    points_threshold = 27.5

    player_stats = fetch_player_stats_by_game(game_date, player_name)
    if player_stats:
        points_scored = player_stats.get('Points', 0)
        recommendation = "p2" if points_scored > points_threshold else "p1"
    else:
        recommendation = "p1"  # Resolve to "No" if no data or player did not play

    print("recommendation:", recommendation)