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
            elif response.status_code == 429:
                time.sleep(backoff * (2 ** i))
            else:
                response.raise_for_status()
        except requests.RequestException as e:
            if i == retries - 1:
                raise ConnectionError(f"Failed to retrieve data from {url}: {e}")

# ─────────── helpers ───────────
def fetch_player_stats(game_id, player_name):
    url = f"https://api.sportsdata.io/v3/nba/stats/json/PlayerGameStatsByGame/{game_id}"
    game_stats = _get(url, "PlayerGameStatsByGame")
    for stat in game_stats:
        if stat["Name"] == player_name:
            return stat
    return None

def find_game_id(date, home_team, away_team):
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date}"
    games = _get(url, "GamesByDate")
    for game in games:
        if game["HomeTeam"] == home_team and game["AwayTeam"] == away_team:
            return game["GameID"]
    return None

# ─────────── main ───────────
def main():
    game_date = "2025-05-22"
    player_name = "Anthony Edwards"
    home_team = "MIN"  # Minnesota Timberwolves
    away_team = "OKC"  # Oklahoma City Thunder

    try:
        game_id = find_game_id(game_date, home_team, away_team)
        if not game_id:
            print("recommendation: p1")  # No game found, resolve to "No"
            return

        player_stats = fetch_player_stats(game_id, player_name)
        if not player_stats:
            print("recommendation: p1")  # Player did not play, resolve to "No"
            return

        points_scored = player_stats.get("Points", 0)
        if points_scored > 24.5:
            print("recommendation: p2")  # Yes, scored more than 24.5 points
        else:
            print("recommendation: p1")  # No, did not score more than 24.5 points

    except Exception as e:
        print(f"An error occurred: {e}")
        print("recommendation: p3")  # Unknown/50-50 due to error

if __name__ == "__main__":
    main()