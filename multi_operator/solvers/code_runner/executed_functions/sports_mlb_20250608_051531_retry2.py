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
GAME_DATE = "2025-06-07"
TEAM1 = "BAL"  # Baltimore Orioles
TEAM2 = "OAK"  # Oakland Athletics

# Resolution map
RESOLUTION_MAP = {
    TEAM1: "p2",  # Orioles win
    TEAM2: "p1",  # Athletics win
    "Canceled": "p3",  # Game canceled
    "Postponed": "p4",  # Game postponed
    "Unknown": "p4"  # Unknown or in-progress
}

def get_game_data(date, team1, team2):
    try:
        # Try proxy endpoint first
        response = requests.get(f"{PROXY_ENDPOINT}/GamesByDate/{date}", headers=HEADERS, timeout=10)
        if not response.ok:
            # Fallback to primary endpoint if proxy fails
            response = requests.get(f"{PRIMARY_ENDPOINT}/GamesByDate/{date}", headers=HEADERS, timeout=10)
        games = response.json()
        for game in games:
            if game["HomeTeam"] == team1 and game["AwayTeam"] == team2:
                return game
            elif game["HomeTeam"] == team2 and game["AwayTeam"] == team1:
                return game
    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
    return None

def resolve_market(game):
    if not game:
        return "recommendation: " + RESOLUTION_MAP["Unknown"]
    if game["Status"] == "Final":
        if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
            winner = game["HomeTeam"]
        else:
            winner = game["AwayTeam"]
        return "recommendation: " + RESOLUTION_MAP.get(winner, "Unknown")
    elif game["Status"] == "Canceled":
        return "recommendation: " + RESOLUTION_MAP["Canceled"]
    elif game["Status"] == "Postponed":
        return "recommendation: " + RESOLUTION_MAP["Postponed"]
    else:
        return "recommendation: " + RESOLUTION_MAP["Unknown"]

# Main execution
game_info = get_game_data(GAME_DATE, TEAM1, TEAM2)
result = resolve_market(game_info)
print(result)