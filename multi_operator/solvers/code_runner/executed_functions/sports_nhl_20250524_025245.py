import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# ─────────── configuration ───────────
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")
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
        except requests.RequestException as e:
            print(f"Request failed: {e}")
    return None

# ─────────── helpers ───────────
def check_mcdavid_goal(game_id):
    url = f"https://api.sportsdata.io/v3/nhl/stats/json/PlayerGameStatsByPlayer/{game_id}/8478402"  # Connor McDavid's Player ID
    game_stats = _get(url, "PlayerGameStats")
    if game_stats and game_stats.get("Goals", 0) >= 1:
        return "p2"  # Yes, scored 1+ goals
    return "p1"  # No goals

def find_game(date_str):
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date_str}"
    games = _get(url, "GamesByDate")
    if games:
        for game in games:
            if game["HomeTeam"] == "DAL" and game["AwayTeam"] == "EDM":
                if game["Status"] == "Scheduled":
                    return game["GameID"]
    return None

# ─────────── main ───────────
if __name__ == "__main__":
    game_date = "2025-05-23"
    game_id = find_game(game_date)
    if game_id:
        recommendation = check_mcdavid_goal(game_id)
    else:
        recommendation = "p1"  # No game found or not scheduled correctly, resolve to "No"
    print("recommendation:", recommendation)