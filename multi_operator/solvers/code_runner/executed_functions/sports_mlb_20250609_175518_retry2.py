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
GAME_DATE = "2025-06-01"
HOME_TEAM = "Giants"
AWAY_TEAM = "Marlins"

# Resolution map
RESOLUTION_MAP = {
    "Giants": "p2",
    "Marlins": "p1",
    "Postponed": "p4",
    "Canceled": "p3",
    "Unknown": "p4"
}

def get_game_data(date):
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        # Fallback to proxy endpoint
        proxy_url = f"{PROXY_ENDPOINT}/GamesByDate/{date}"
        response = requests.get(proxy_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()

def resolve_market(games, home_team, away_team):
    for game in games:
        if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
            if game['Status'] == "Final":
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return RESOLUTION_MAP[home_team]
                else:
                    return RESOLUTION_MAP[away_team]
            elif game['Status'] == "Postponed":
                return RESOLUTION_MAP["Postponed"]
            elif game['Status'] == "Canceled":
                return RESOLUTION_MAP["Canceled"]
    return RESOLUTION_MAP["Unknown"]

if __name__ == "__main__":
    games = get_game_data(GAME_DATE)
    recommendation = resolve_market(games, HOME_TEAM, AWAY_TEAM)
    print(f"recommendation: {recommendation}")