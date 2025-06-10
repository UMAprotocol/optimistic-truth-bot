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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Game details
GAME_DATE = "2025-06-04"
TEAM1 = "MIL"  # Milwaukee Brewers
TEAM2 = "CIN"  # Cincinnati Reds

# Resolution map
RESOLUTION_MAP = {
    TEAM1: "p2",  # Brewers win
    TEAM2: "p1",  # Reds win
    "Postponed": "p4",  # Game postponed
    "Canceled": "p3",  # Game canceled
    "Unknown": "p4"  # Unknown or in-progress
}

def get_game_data(date):
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] == TEAM2 and game['AwayTeam'] == TEAM1:
                return game
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error accessing primary endpoint: {e}")
        try:
            response = requests.get(f"{PROXY_ENDPOINT}/mlb/GamesByDate/{date}", timeout=10)
            response.raise_for_status()
            games = response.json()
            for game in games:
                if game['HomeTeam'] == TEAM2 and game['AwayTeam'] == TEAM1:
                    return game
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error accessing proxy endpoint: {e}")
            return None

def resolve_market(game):
    if not game:
        return "recommendation: " + RESOLUTION_MAP["Unknown"]
    if game['Status'] == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            return "recommendation: " + RESOLUTION_MAP[TEAM2]
        elif game['AwayTeamRuns'] > game['HomeTeamRuns']:
            return "recommendation: " + RESOLUTION_MAP[TEAM1]
    elif game['Status'] == "Postponed":
        return "recommendation: " + RESOLUTION_MAP["Postponed"]
    elif game['Status'] == "Canceled":
        return "recommendation: " + RESOLUTION_MAP["Canceled"]
    return "recommendation: " + RESOLUTION_MAP["Unknown"]

if __name__ == "__main__":
    game_info = get_game_data(GAME_DATE)
    result = resolve_market(game_info)
    print(result)