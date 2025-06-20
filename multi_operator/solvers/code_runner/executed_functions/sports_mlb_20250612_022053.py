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
            if response.status_code in {401, 403, 404, 429}:
                wait = backoff * 2**i
                time.sleep(wait)
                continue
            response.raise_for_status()
        except requests.RequestException as e:
            if i == retries - 1:
                raise ConnectionError(f"Failed to retrieve data from {url}: {e}")
            time.sleep(backoff * 2**i)

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
    game_date = datetime(2025, 6, 11)
    player_name = "Tyrese Haliburton"
    points_threshold = 17.5

    try:
        player_stats = fetch_player_stats(game_date, player_name)
        if player_stats and player_stats.get("Points") is not None:
            points_scored = player_stats["Points"]
            recommendation = "p2" if points_scored > points_threshold else "p1"
        else:
            recommendation = "p1"  # Resolve to "No" if no data or player did not play
    except Exception as e:
        print(f"Error occurred: {e}")
        recommendation = "p3"  # Resolve to unknown/50-50 if there's an error fetching data

    print("recommendation:", recommendation)

if __name__ == "__main__":
    main()