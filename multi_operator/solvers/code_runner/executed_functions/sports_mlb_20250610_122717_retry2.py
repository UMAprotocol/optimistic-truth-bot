import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not MLB_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API configuration
HEADERS = {"Ocp-Apim-Subscription-Key": MLB_API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "Braves": "p2",  # Atlanta Braves win
    "Brewers": "p1",  # Milwaukee Brewers win
    "Postponed": "p4",  # Game postponed
    "Canceled": "p3"  # Game canceled
}

def get_game_data(date, home_team, away_team):
    # Try proxy endpoint first
    url = f"{PROXY_ENDPOINT}/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS, timeout=10)
    if not response.ok:
        # Fallback to primary endpoint if proxy fails
        url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        if not response.ok:
            return None
    games = response.json()
    for game in games:
        if game["HomeTeam"] == home_team and game["AwayTeam"] == away_team:
            return game
    return None

def resolve_market(game):
    if not game:
        return "recommendation: p4"  # No game data found
    if game["Status"] == "Final":
        if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
            return f"recommendation: {RESOLUTION_MAP[game['HomeTeam']]}"
        else:
            return f"recommendation: {RESOLUTION_MAP[game['AwayTeam']]}"
    elif game["Status"] in ["Postponed", "Canceled"]:
        return f"recommendation: {RESOLUTION_MAP[game['Status']]}"
    else:
        return "recommendation: p4"  # Game not completed or other status

if __name__ == "__main__":
    # Game details
    game_date = "2025-06-09"
    home_team = "Brewers"  # Milwaukee Brewers
    away_team = "Braves"  # Atlanta Braves

    # Fetch game data and resolve market
    game_info = get_game_data(game_date, home_team, away_team)
    result = resolve_market(game_info)
    print(result)