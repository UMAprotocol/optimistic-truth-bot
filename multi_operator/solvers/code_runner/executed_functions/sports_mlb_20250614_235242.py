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
GAME_DATE = "2025-06-14"
HOME_TEAM = "Texas Rangers"
AWAY_TEAM = "Chicago White Sox"

# Resolution map
RESOLUTION_MAP = {
    "Texas Rangers": "p1",
    "Chicago White Sox": "p2",
    "Postponed": "p4",
    "Canceled": "p3"
}

def get_game_data(date):
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Primary endpoint failed: {e}")
        try:
            # Fallback to proxy endpoint
            proxy_url = f"{PROXY_ENDPOINT}/GamesByDate/{date}"
            response = requests.get(proxy_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Proxy endpoint also failed: {e}")
            return None

def resolve_market(games, home_team, away_team):
    for game in games:
        if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
            if game['Status'] == "Final":
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    return RESOLUTION_MAP[home_team]
                elif game['AwayTeamRuns'] > game['HomeTeamRuns']:
                    return RESOLUTION_MAP[away_team]
            elif game['Status'] == "Postponed":
                return RESOLUTION_MAP["Postponed"]
            elif game['Status'] == "Canceled":
                return RESOLUTION_MAP["Canceled"]
    return "p4"  # Game not found or in progress

if __name__ == "__main__":
    games = get_game_data(GAME_DATE)
    if games:
        recommendation = resolve_market(games, HOME_TEAM, AWAY_TEAM)
        print(f"recommendation: {recommendation}")
    else:
        print("recommendation: p4")  # Unable to retrieve game data