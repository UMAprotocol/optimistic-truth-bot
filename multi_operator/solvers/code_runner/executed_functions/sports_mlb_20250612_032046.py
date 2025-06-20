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
    formatted_date = game_date.strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/nba/stats/json/PlayerGameStatsByDate/{formatted_date}"
    games = _get(url, "PlayerGameStatsByDate")
    if games:
        for game in games:
            if game['Name'] == player_name:
                return game
    return None

# ─────────── main ───────────
def main():
    game_date = datetime(2025, 6, 11)
    player_name = "Shai Gilgeous-Alexander"
    player_stats = fetch_player_stats(game_date, player_name)
    if player_stats:
        points_scored = player_stats.get('Points', 0)
        if points_scored > 34.5:
            print("recommendation: p2")  # Yes, scored more than 34.5 points
        else:
            print("recommendation: p1")  # No, did not score more than 34.5 points
    else:
        print("recommendation: p1")  # No data found or player did not play

if __name__ == "__main__":
    main()