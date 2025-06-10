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
            if response.status_code == 429:
                time.sleep(backoff * (2 ** i))
        except requests.RequestException as e:
            if i == retries - 1:
                raise ConnectionError(f"Failed to retrieve data from {url}: {e}")
    return None

# ─────────── helpers ───────────
def fetch_player_stats(game_date, player_name):
    formatted_date = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/nba/stats/json/PlayerGameStatsByDate/{formatted_date}"
    games = _get(url, "PlayerGameStatsByDate")
    if games:
        for game in games:
            if game['Name'] == player_name:
                return game
    return None

# ─────────── main ───────────
if __name__ == "__main__":
    GAME_DATE = "2025-05-29"
    PLAYER_NAME = "Tyrese Haliburton"
    POINTS_THRESHOLD = 22.5

    player_stats = fetch_player_stats(GAME_DATE, PLAYER_NAME)
    if player_stats and player_stats.get("Points") is not None:
        recommendation = "p2" if player_stats["Points"] > POINTS_THRESHOLD else "p1"
    else:
        recommendation = "p1"  # Resolve to "No" if game data is missing or player did not play

    print("recommendation:", recommendation)