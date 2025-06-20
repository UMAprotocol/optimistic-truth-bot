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
GAME_DATE = "2025-06-13"
HOME_TEAM = "Cubs"
AWAY_TEAM = "Pirates"

# Resolution map
RESOLUTION_MAP = {
    "Cubs": "p1",
    "Pirates": "p2",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_game_data(date):
    """Fetch game data for a specific date."""
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
    """Resolve the market based on game results."""
    for game in games:
        if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
            if game['Status'] == "Final":
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    return RESOLUTION_MAP[home_team]
                elif game['AwayTeamRuns'] > game['HomeTeamRuns']:
                    return RESOLUTION_MAP[away_team]
            elif game['Status'] in ["Canceled", "Postponed"]:
                return RESOLUTION_MAP["50-50"]
    return RESOLUTION_MAP["Too early to resolve"]

def main():
    games = get_game_data(GAME_DATE)
    if games:
        recommendation = resolve_market(games, HOME_TEAM, AWAY_TEAM)
        print(f"recommendation: {recommendation}")
    else:
        print("recommendation: p4")

if __name__ == "__main__":
    main()