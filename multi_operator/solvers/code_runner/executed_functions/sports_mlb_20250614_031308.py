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
def fetch_player_stats(game_date, player_name):
    formatted_date = game_date.strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/nba/stats/json/PlayerGameStatsByDate/{formatted_date}"
    games = _get(url, "PlayerGameStatsByDate")
    if games:
        for game in games:
            if game["Name"] == player_name:
                return game
    return None

# ─────────── main ───────────
def main():
    GAME_DATE = datetime(2025, 6, 13)
    PLAYER_NAME = "Tyrese Haliburton"
    THRESHOLD_POINTS = 17.5

    try:
        player_stats = fetch_player_stats(GAME_DATE, PLAYER_NAME)
        if player_stats and player_stats.get("Points") is not None:
            points_scored = player_stats["Points"]
            recommendation = "p2" if points_scored > THRESHOLD_POINTS else "p1"
        else:
            recommendation = "p1"  # Game not played or data not available
    except Exception as e:
        print(f"Error occurred: {e}")
        recommendation = "p1"  # Default to "No" in case of errors

    print("recommendation:", recommendation)

if __name__ == "__main__":
    main()