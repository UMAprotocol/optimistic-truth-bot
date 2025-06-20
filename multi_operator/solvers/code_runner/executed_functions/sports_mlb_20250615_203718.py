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
GAME_DATE = "2025-06-15"
HOME_TEAM = "PHI"  # Philadelphia Phillies
AWAY_TEAM = "TOR"  # Toronto Blue Jays

# Resolution map
RESOLUTION_MAP = {
    "Blue Jays": "p2",
    "Phillies": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_game_data(date):
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] == HOME_TEAM and game['AwayTeam'] == AWAY_TEAM:
                return game
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        try:
            response = requests.get(f"{PROXY_ENDPOINT}/GamesByDate/{date}", headers=HEADERS, timeout=10)
            response.raise_for_status()
            games = response.json()
            for game in games:
                if game['HomeTeam'] == HOME_TEAM and game['AwayTeam'] == AWAY_TEAM:
                    return game
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
    return None

def resolve_market(game):
    if not game:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    if game['Status'] == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            return "recommendation: " + RESOLUTION_MAP["Phillies"]
        elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
            return "recommendation: " + RESOLUTION_MAP["Blue Jays"]
    elif game['Status'] == "Canceled":
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    elif game['Status'] == "Postponed":
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    game_info = get_game_data(GAME_DATE)
    result = resolve_market(game_info)
    print(result)