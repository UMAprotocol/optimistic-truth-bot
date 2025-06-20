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
GAME_DATE = "2025-06-11"
HOME_TEAM = "BOS"
AWAY_TEAM = "TBR"

# Resolution map
RESOLUTION_MAP = {
    "BOS": "p1",  # Red Sox win
    "TBR": "p2",  # Rays win
    "Postponed": "p4",  # Game postponed
    "Canceled": "p3",  # Game canceled
    "Scheduled": "p4"  # Game scheduled but not yet played
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
    except requests.exceptions.RequestException as e:
        print(f"Error accessing primary endpoint: {e}")
        try:
            response = requests.get(f"{PROXY_ENDPOINT}/GamesByDate/{date}", timeout=10)
            response.raise_for_status()
            games = response.json()
            for game in games:
                if game["HomeTeam"] == HOME_TEAM and game["AwayTeam"] == AWAY_TEAM:
                    return game
        except requests.exceptions.RequestException as e:
            print(f"Error accessing proxy endpoint: {e}")
    return None

def resolve_market(game):
    if not game:
        return "recommendation: p4"  # No data available
    status = game["Status"]
    if status == "Final":
        if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
            return f"recommendation: {RESOLUTION_MAP[HOME_TEAM]}"
        elif game["AwayTeamRuns"] > game["HomeTeamRuns"]:
            return f"recommendation: {RESOLUTION_MAP[AWAY_TEAM]}"
    return f"recommendation: {RESOLUTION_MAP.get(status, 'p4')}"

if __name__ == "__main__":
    game_info = get_game_data(GAME_DATE)
    result = resolve_market(game_info)
    print(result)