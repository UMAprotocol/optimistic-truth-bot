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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy"

# Game details
GAME_DATE = "2025-06-04"
HOME_TEAM = "STL"  # St. Louis Cardinals
AWAY_TEAM = "KC"   # Kansas City Royals

# Resolution map
RESOLUTION_MAP = {
    HOME_TEAM: "p1",  # Cardinals win
    AWAY_TEAM: "p2",  # Royals win
    "Canceled": "p3",  # Game canceled
    "Postponed": "p4",  # Game postponed
    "Unknown": "p4"   # Unknown or in-progress
}

def get_game_data(date):
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game["HomeTeam"] == HOME_TEAM and game["AwayTeam"] == AWAY_TEAM:
                return game
    except requests.RequestException:
        try:
            # Fallback to proxy endpoint
            response = requests.get(f"{PROXY_ENDPOINT}/GamesByDate/{date}", headers=HEADERS, timeout=10)
            response.raise_for_status()
            games = response.json()
            for game in games:
                if game["HomeTeam"] == HOME_TEAM and game["AwayTeam"] == AWAY_TEAM:
                    return game
        except requests.RequestException:
            pass
    return None

def resolve_market(game):
    if not game:
        return "recommendation: " + RESOLUTION_MAP["Unknown"]
    if game["Status"] == "Final":
        if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
            return "recommendation: " + RESOLUTION_MAP[HOME_TEAM]
        elif game["AwayTeamRuns"] > game["HomeTeamRuns"]:
            return "recommendation: " + RESOLUTION_MAP[AWAY_TEAM]
    elif game["Status"] == "Canceled":
        return "recommendation: " + RESOLUTION_MAP["Canceled"]
    elif game["Status"] == "Postponed":
        return "recommendation: " + RESOLUTION_MAP["Postponed"]
    return "recommendation: " + RESOLUTION_MAP["Unknown"]

if __name__ == "__main__":
    game_info = get_game_data(GAME_DATE)
    result = resolve_market(game_info)
    print(result)