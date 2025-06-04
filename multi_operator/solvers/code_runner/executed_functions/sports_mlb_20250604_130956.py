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
GAME_DATE = "2025-06-01"
HOME_TEAM = "Mariners"
AWAY_TEAM = "Twins"

# Resolution map
RESOLUTION_MAP = {
    "Mariners": "p1",
    "Twins": "p2",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_game_data(date, home_team, away_team):
    # Try proxy endpoint first
    url = f"{PROXY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            games = response.json()
        else:
            raise Exception("Proxy failed")
    except:
        # Fallback to primary endpoint
        url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        games = response.json()

    # Find the game
    for game in games:
        if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
            return game
    return None

def resolve_market(game):
    if not game:
        return RESOLUTION_MAP["Too early to resolve"]
    if game['Status'] == 'Final':
        home_score = game['HomeTeamRuns']
        away_score = game['AwayTeamRuns']
        if home_score > away_score:
            return RESOLUTION_MAP[HOME_TEAM]
        elif away_score > home_score:
            return RESOLUTION_MAP[AWAY_TEAM]
    elif game['Status'] in ['Canceled', 'Postponed']:
        return RESOLUTION_MAP["50-50"]
    return RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    game_info = get_game_data(GAME_DATE, HOME_TEAM, AWAY_TEAM)
    result = resolve_market(game_info)
    print(f"recommendation: {result}")