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

# Game details
GAME_DATE = "2025-05-27"
HOME_TEAM = "PHI"  # Philadelphia Phillies
AWAY_TEAM = "ATL"  # Atlanta Braves

# Resolution map
RESOLUTION_MAP = {
    HOME_TEAM: "p1",  # Phillies win
    AWAY_TEAM: "p2",  # Braves win
    "Canceled": "p3",  # Game canceled
    "Postponed": "p4",  # Game postponed
    "Scheduled": "p4",  # Game not yet played
    "InProgress": "p4",  # Game in progress
}

def get_game_data(date):
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        # Fallback to proxy endpoint
        url = f"{PROXY_ENDPOINT}/GamesByDate/{date}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()

def resolve_market(games):
    for game in games:
        if game['HomeTeam'] == HOME_TEAM and game['AwayTeam'] == AWAY_TEAM:
            status = game['Status']
            if status == "Final":
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return RESOLUTION_MAP[HOME_TEAM]
                elif away_score > home_score:
                    return RESOLUTION_MAP[AWAY_TEAM]
            else:
                return RESOLUTION_MAP.get(status, "p4")
    return "p4"

if __name__ == "__main__":
    games = get_game_data(GAME_DATE)
    result = resolve_market(games)
    print(f"recommendation: {result}")