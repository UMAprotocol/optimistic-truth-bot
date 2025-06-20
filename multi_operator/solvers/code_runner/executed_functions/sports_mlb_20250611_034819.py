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
GAME_DATE = "2025-06-10"
HOME_TEAM = "Rockies"
AWAY_TEAM = "Giants"

# Resolution map
RESOLUTION_MAP = {
    "Rockies": "p1",
    "Giants": "p2",
    "Postponed": "p4",
    "Canceled": "p3"
}

def get_game_data(date):
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        try:
            # Fallback to proxy endpoint
            proxy_url = f"{PROXY_ENDPOINT}/GamesByDate/{date}"
            response = requests.get(proxy_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Failed to retrieve data from both primary and proxy endpoints: {e}")
            return None

def resolve_market(games):
    for game in games:
        if game['HomeTeam'] == HOME_TEAM and game['AwayTeam'] == AWAY_TEAM:
            if game['Status'] == "Final":
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    return RESOLUTION_MAP[HOME_TEAM]
                elif game['AwayTeamRuns'] > game['HomeTeamRuns']:
                    return RESOLUTION_MAP[AWAY_TEAM]
            elif game['Status'] in ["Postponed", "Canceled"]:
                return RESOLUTION_MAP[game['Status']]
    return "p4"  # If no game matches or game is still scheduled/in progress

if __name__ == "__main__":
    games = get_game_data(GAME_DATE)
    if games:
        recommendation = resolve_market(games)
    else:
        recommendation = "p4"  # Unable to retrieve game data
    print(f"recommendation: {recommendation}")