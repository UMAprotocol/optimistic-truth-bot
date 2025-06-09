import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API configuration
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/mlb"

# Game details
GAME_DATE = "2025-06-06"
TEAMS = {"Cubs": "CHC", "Tigers": "DET"}

# Resolution map
RESOLUTION_MAP = {
    "CHC": "p2",  # Chicago Cubs win
    "DET": "p1",  # Detroit Tigers win
    "Canceled": "p3",  # Game canceled
    "Postponed": "p4",  # Game postponed or in-progress
    "Unknown": "p4"  # Unknown or not enough data
}

def get_game_data(date, team1, team2):
    # Try proxy endpoint first
    url = f"{PROXY_ENDPOINT}/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS, timeout=10)
    if not response.ok:
        # Fallback to primary endpoint
        url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
        response = requests.get(url, headers=HEADERS, timeout=10)
    if response.ok:
        games = response.json()
        for game in games:
            if game["HomeTeam"] == team1 and game["AwayTeam"] == team2:
                return game
            if game["HomeTeam"] == team2 and game["AwayTeam"] == team1:
                return game
    return None

def resolve_market(game):
    if not game:
        return "recommendation: " + RESOLUTION_MAP["Unknown"]
    if game["Status"] == "Final":
        if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
            return "recommendation: " + RESOLUTION_MAP[game["HomeTeam"]]
        else:
            return "recommendation: " + RESOLUTION_MAP[game["AwayTeam"]]
    elif game["Status"] == "Canceled":
        return "recommendation: " + RESOLUTION_MAP["Canceled"]
    elif game["Status"] == "Postponed":
        return "recommendation: " + RESOLUTION_MAP["Postponed"]
    else:
        return "recommendation: " + RESOLUTION_MAP["Unknown"]

if __name__ == "__main__":
    game_info = get_game_data(GAME_DATE, TEAMS["Cubs"], TEAMS["Tigers"])
    result = resolve_market(game_info)
    print(result)