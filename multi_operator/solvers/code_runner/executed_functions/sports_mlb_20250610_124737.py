import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/mlb"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "Marlins": "p2",
    "Pirates": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_game_data(date, team1, team2):
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
        if (game["HomeTeam"] == team1 and game["AwayTeam"] == team2) or \
           (game["HomeTeam"] == team2 and game["AwayTeam"] == team1):
            return game
    return None

def resolve_market(game):
    if not game:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    if game["Status"] == "Final":
        if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
            winner = game["HomeTeam"]
        else:
            winner = game["AwayTeam"]
        return "recommendation: " + RESOLUTION_MAP[winner]
    elif game["Status"] in ["Canceled", "Postponed"]:
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    else:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    # Game details
    game_date = "2025-06-09"
    home_team = "Marlins"
    away_team = "Pirates"

    # Get game data
    game = get_game_data(game_date, home_team, away_team)

    # Resolve the market based on the game data
    result = resolve_market(game)
    print(result)